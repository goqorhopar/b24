const TelegramBot = require('node-telegram-bot-api');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const BITRIX_WEBHOOK_URL = process.env.BITRIX_WEBHOOK_URL;
const ADMIN_CHAT_ID = process.env.ADMIN_CHAT_ID;

if (!TELEGRAM_BOT_TOKEN) {
    console.error('❌ TELEGRAM_BOT_TOKEN не найден');
    process.exit(1);
}

console.log('🤖 Запуск Meeting Bot Assistant...');
const bot = new TelegramBot(TELEGRAM_BOT_TOKEN, { polling: true });

// MCP Router process
let mcpProcess = null;

// Start MCP Router
function startMCPRouter() {
    try {
        const routerPath = path.join(__dirname, 'router.py');
        console.log(`🚀 Запуск MCP Router: ${routerPath}`);
        
        mcpProcess = spawn('python3', [routerPath], {
            stdio: ['pipe', 'pipe', 'pipe'],
            cwd: __dirname
        });

        mcpProcess.stdout.on('data', (data) => {
            console.log(`MCP Router stdout: ${data}`);
        });

        mcpProcess.stderr.on('data', (data) => {
            console.log(`MCP Router stderr: ${data}`);
        });

        mcpProcess.on('close', (code) => {
            console.log(`MCP Router завершился с кодом ${code}`);
            // Restart after 5 seconds
            setTimeout(() => {
                console.log('🔄 Перезапуск MCP Router...');
                startMCPRouter();
            }, 5000);
        });

        mcpProcess.on('error', (error) => {
            console.error(`Ошибка MCP Router: ${error}`);
        });

        console.log('✅ MCP Router запущен');
    } catch (error) {
        console.error(`❌ Ошибка запуска MCP Router: ${error}`);
    }
}

// Send MCP request
function sendMCPRequest(method, params = {}) {
    return new Promise((resolve, reject) => {
        if (!mcpProcess || mcpProcess.killed) {
            reject(new Error('MCP Router не запущен'));
            return;
        }

        const request = {
            jsonrpc: '2.0',
            id: Date.now(),
            method: method,
            params: params
        };

        let responseData = '';
        let timeout;

        const onData = (data) => {
            responseData += data.toString();
            try {
                const response = JSON.parse(responseData);
                clearTimeout(timeout);
                mcpProcess.stdout.removeListener('data', onData);
                resolve(response);
            } catch (e) {
                // Continue accumulating data
            }
        };

        mcpProcess.stdout.on('data', onData);

        timeout = setTimeout(() => {
            mcpProcess.stdout.removeListener('data', onData);
            reject(new Error('Timeout waiting for MCP response'));
        }, 30000);

        mcpProcess.stdin.write(JSON.stringify(request) + '\n');
    });
}

// User states for conversation flow
const userStates = new Map();

bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text || '';
    const user = msg.from;
    const userId = user.id;

    console.log(`📨 Сообщение от ${user.username || user.first_name}: ${text}`);

    try {
        if (text.startsWith('/start')) {
            await bot.sendMessage(chatId,
                '🤖 **Meeting Bot Assistant**\n\n' +
                'Я автоматический ассистент для встреч!\n\n' +
                '**Доступные команды:**\n' +
                '• Отправь ссылку на встречу (Zoom, Google Meet, Teams)\n' +
                '• /checklist - получить чеклист для встречи\n' +
                '• /status - статус системы\n\n' +
                '**Как это работает:**\n' +
                '1. Отправь ссылку на встречу\n' +
                '2. Я присоединюсь и начну запись\n' +
                '3. После встречи проанализирую транскрипт\n' +
                '4. Обновлю лид в Bitrix24\n' +
                '5. Создам задачи и следующие шаги',
                { parse_mode: 'Markdown' }
            );
            userStates.set(userId, { state: 'waiting_for_meeting' });
        }
        else if (text.startsWith('/checklist')) {
            await bot.sendMessage(chatId, '📋 Введите тип встречи (sales, demo, follow-up):');
            userStates.set(userId, { state: 'waiting_for_meeting_type' });
        }
        else if (text.startsWith('/status')) {
            const status = mcpProcess && !mcpProcess.killed ? '🟢 Работает' : '🔴 Не работает';
            await bot.sendMessage(chatId,
                `📊 **Статус системы:**\n\n` +
                `MCP Router: ${status}\n` +
                `Gemini API: ${GEMINI_API_KEY ? '🟢 Настроен' : '🔴 Не настроен'}\n` +
                `Bitrix24: ${BITRIX_WEBHOOK_URL ? '🟢 Настроен' : '🔴 Не настроен'}\n` +
                `Telegram Bot: 🟢 Работает`,
                { parse_mode: 'Markdown' }
            );
        }
        else if (userStates.get(userId)?.state === 'waiting_for_meeting_type') {
            const meetingType = text.toLowerCase();
            if (['sales', 'demo', 'follow-up'].includes(meetingType)) {
                await bot.sendMessage(chatId, '⏳ Генерирую чеклист...');
                
                try {
                    const response = await sendMCPRequest('tools/call', {
                        name: 'checklist_generation',
                        arguments: {
                            meeting_type: meetingType,
                            lead_info: 'Новый лид',
                            industry: 'IT'
                        }
                    });

                    if (response.result && response.result.checklist) {
                        const checklist = response.result.checklist;
                        let message = `📋 **Чеклист для ${meetingType} встречи:**\n\n`;
                        
                        message += `**Подготовка:**\n`;
                        checklist.pre_meeting?.forEach((item, index) => {
                            message += `${index + 1}. ${item}\n`;
                        });
                        
                        message += `\n**Во время встречи:**\n`;
                        checklist.during_meeting?.forEach((item, index) => {
                            message += `${index + 1}. ${item}\n`;
                        });
                        
                        message += `\n**После встречи:**\n`;
                        checklist.post_meeting?.forEach((item, index) => {
                            message += `${index + 1}. ${item}\n`;
                        });

                        await bot.sendMessage(chatId, message, { parse_mode: 'Markdown' });
                    } else {
                        await bot.sendMessage(chatId, '❌ Ошибка генерации чеклиста');
                    }
                } catch (error) {
                    console.error('Ошибка генерации чеклиста:', error);
                    await bot.sendMessage(chatId, '❌ Ошибка генерации чеклиста');
                }
                
                userStates.set(userId, { state: 'waiting_for_meeting' });
            } else {
                await bot.sendMessage(chatId, '❌ Неверный тип встречи. Используйте: sales, demo, follow-up');
            }
        }
        else if (text.includes('meet.google.com') || text.includes('zoom.us') || text.includes('teams.microsoft.com')) {
            await bot.sendMessage(chatId, '🚀 Получил ссылку на встречу! Присоединяюсь...');
            
            try {
                // Determine platform
                let platform = 'generic';
                if (text.includes('zoom.us')) platform = 'zoom';
                else if (text.includes('meet.google.com')) platform = 'meet';
                else if (text.includes('teams.microsoft.com')) platform = 'teams';

                // Join meeting
                const joinResponse = await sendMCPRequest('tools/call', {
                    name: 'meeting_join',
                    arguments: {
                        meeting_url: text,
                        platform: platform,
                        auto_join: true
                    }
                });

                if (joinResponse.result && joinResponse.result.status === 'joined') {
                    await bot.sendMessage(chatId,
                        '✅ **Встреча обработана!**\n\n' +
                        `Платформа: ${platform}\n` +
                        `Время присоединения: ${joinResponse.result.join_time}\n` +
                        `Запись: ${joinResponse.result.recording_started ? 'Запущена' : 'Не запущена'}\n\n` +
                        'Введите ID лида для обновления в Bitrix24:'
                    );
                    userStates.set(userId, { 
                        state: 'waiting_for_lead_id',
                        meeting_url: text,
                        platform: platform,
                        meeting_id: joinResponse.result.meeting_id
                    });
                } else {
                    await bot.sendMessage(chatId, '❌ Не удалось присоединиться к встрече');
                }
            } catch (error) {
                console.error('Ошибка присоединения к встрече:', error);
                await bot.sendMessage(chatId, '❌ Ошибка присоединения к встрече');
            }
        }
        else if (userStates.get(userId)?.state === 'waiting_for_lead_id' && /^\d+$/.test(text)) {
            const leadId = text;
            const userState = userStates.get(userId);
            
            await bot.sendMessage(chatId, '⏳ Обновляю лид в Bitrix24...');
            
            try {
                // Simulate meeting analysis (in real scenario, this would be done after meeting ends)
                const analysisResponse = await sendMCPRequest('tools/call', {
                    name: 'meeting_analyze',
                    arguments: {
                        transcript: 'Встреча прошла успешно. Обсудили требования клиента, представили решение, договорились о следующих шагах.',
                        meeting_url: userState.meeting_url,
                        lead_id: leadId
                    }
                });

                if (analysisResponse.result && analysisResponse.result.analysis) {
                    const analysis = analysisResponse.result.analysis;
                    
                    // Update Bitrix24
                    const updateResponse = await sendMCPRequest('tools/call', {
                        name: 'bitrix_update',
                        arguments: {
                            lead_id: leadId,
                            summary: analysis.summary,
                            tasks: analysis.action_items || [],
                            status: 'MEETING_COMPLETED'
                        }
                    });

                    if (updateResponse.result && updateResponse.result.status === 'updated') {
                        await bot.sendMessage(chatId,
                            `✅ **Лид ${leadId} обновлен в Bitrix24!**\n\n` +
                            `**Краткое резюме:**\n${analysis.summary}\n\n` +
                            `**Оценка лида:** ${analysis.lead_score}/10\n\n` +
                            `**Создано задач:** ${updateResponse.result.tasks_created}\n\n` +
                            `**Следующие шаги:**\n${analysis.next_steps?.join('\n') || 'Не определены'}`
                        );
                    } else {
                        await bot.sendMessage(chatId, '❌ Ошибка обновления лида в Bitrix24');
                    }
                } else {
                    await bot.sendMessage(chatId, '❌ Ошибка анализа встречи');
                }
            } catch (error) {
                console.error('Ошибка обработки лида:', error);
                await bot.sendMessage(chatId, '❌ Ошибка обработки лида');
            }
            
            userStates.set(userId, { state: 'waiting_for_meeting' });
        }
        else {
            await bot.sendMessage(chatId,
                '👋 Привет! Отправь ссылку на встречу или используй /start\n\n' +
                '**Доступные команды:**\n' +
                '• /checklist - получить чеклист\n' +
                '• /status - статус системы'
            );
        }
    } catch (error) {
        console.error('❌ Ошибка:', error);
        await bot.sendMessage(chatId, '❌ Произошла ошибка при обработке сообщения.');
    }
});

// Handle errors
bot.on('error', (error) => {
    console.error('❌ Ошибка Telegram бота:', error);
});

bot.on('polling_error', (error) => {
    console.error('❌ Ошибка polling:', error);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('🛑 Остановка бота...');
    if (mcpProcess) {
        mcpProcess.kill();
    }
    bot.stopPolling();
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('🛑 Остановка бота...');
    if (mcpProcess) {
        mcpProcess.kill();
    }
    bot.stopPolling();
    process.exit(0);
});

// Start MCP Router
startMCPRouter();

console.log('✅ Meeting Bot Assistant запущен!');