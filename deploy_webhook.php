<?php
/**
 * GitHub Webhook для автодеплоя на VPS Beget
 * Разместите этот файл в корне вашего веб-сервера
 */

// Настройки
$secret = 'your-secret-key-here'; // Замените на ваш секретный ключ
$project_path = '/opt/telegram-bot';
$log_file = '/var/log/deploy.log';

// Функция для логирования
function log_message($message) {
    global $log_file;
    $timestamp = date('Y-m-d H:i:s');
    file_put_contents($log_file, "[$timestamp] $message\n", FILE_APPEND | LOCK_EX);
}

// Получаем payload
$payload = file_get_contents('php://input');
$sig_header = $_SERVER['HTTP_X_HUB_SIGNATURE_256'] ?? '';

// Проверяем подпись
if (!hash_equals('sha256=' . hash_hmac('sha256', $payload, $secret), $sig_header)) {
    http_response_code(401);
    log_message('Unauthorized webhook request');
    exit('Unauthorized');
}

// Парсим JSON
$data = json_decode($payload, true);
if (!$data) {
    http_response_code(400);
    log_message('Invalid JSON payload');
    exit('Invalid JSON');
}

// Проверяем, что это push в main ветку
$ref = $data['ref'] ?? '';
$branch = str_replace('refs/heads/', '', $ref);

if ($branch !== 'main' && $branch !== 'master') {
    log_message("Ignoring push to branch: $branch");
    exit('Ignoring branch');
}

log_message("Starting deployment for branch: $branch");

try {
    // Переходим в директорию проекта
    chdir($project_path);
    
    // Останавливаем сервис
    log_message('Stopping telegram-bot service...');
    shell_exec('systemctl stop telegram-bot 2>&1');
    
    // Pull изменений
    log_message('Pulling latest changes...');
    $git_output = shell_exec('git pull origin main 2>&1');
    log_message("Git output: $git_output");
    
    // Активируем виртуальное окружение и обновляем зависимости
    log_message('Updating dependencies...');
    $pip_output = shell_exec('source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt 2>&1');
    log_message("Pip output: $pip_output");
    
    // Перезапускаем сервис
    log_message('Starting telegram-bot service...');
    shell_exec('systemctl daemon-reload 2>&1');
    shell_exec('systemctl start telegram-bot 2>&1');
    
    // Проверяем статус
    $status = shell_exec('systemctl is-active telegram-bot 2>&1');
    if (trim($status) === 'active') {
        log_message('Deployment completed successfully');
        
        // Отправляем уведомление в Telegram (опционально)
        $telegram_token = 'YOUR_BOT_TOKEN';
        $chat_id = 'YOUR_CHAT_ID';
        $message = "✅ Деплой завершен успешно!\nВетка: $branch\nВремя: " . date('Y-m-d H:i:s');
        
        $telegram_url = "https://api.telegram.org/bot$telegram_token/sendMessage";
        $telegram_data = [
            'chat_id' => $chat_id,
            'text' => $message
        ];
        
        $context = stream_context_create([
            'http' => [
                'method' => 'POST',
                'header' => 'Content-Type: application/json',
                'content' => json_encode($telegram_data)
            ]
        ]);
        
        file_get_contents($telegram_url, false, $context);
        
    } else {
        log_message('Service failed to start');
        throw new Exception('Service failed to start');
    }
    
} catch (Exception $e) {
    log_message('Deployment failed: ' . $e->getMessage());
    http_response_code(500);
    exit('Deployment failed');
}

http_response_code(200);
echo 'Deployment successful';
?>
