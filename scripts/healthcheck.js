#!/usr/bin/env node

/**
 * Health check script for Docker container
 */

const http = require('http')
const config = require('../src/config')

const HEALTH_CHECK_URL = `http://localhost:${config.PORT}/health`
const TIMEOUT = 5000

function performHealthCheck() {
  return new Promise((resolve, reject) => {
    const req = http.get(HEALTH_CHECK_URL, { timeout: TIMEOUT }, (res) => {
      let data = ''

      res.on('data', (chunk) => {
        data += chunk
      })

      res.on('end', () => {
        try {
          const health = JSON.parse(data)
          
          if (res.statusCode === 200 && health.status === 'healthy') {
            resolve({
              success: true,
              status: health.status,
              timestamp: health.timestamp
            })
          } else {
            reject(new Error(`Health check failed: ${health.status} (${res.statusCode})`))
          }
        } catch (error) {
          reject(new Error(`Invalid health check response: ${error.message}`))
        }
      })
    })

    req.on('error', (error) => {
      reject(new Error(`Health check request failed: ${error.message}`))
    })

    req.on('timeout', () => {
      req.destroy()
      reject(new Error('Health check timeout'))
    })
  })
}

async function main() {
  try {
    console.log('🏥 Performing health check...')
    
    const result = await performHealthCheck()
    
    console.log('✅ Health check passed')
    console.log(`Status: ${result.status}`)
    console.log(`Timestamp: ${result.timestamp}`)
    
    process.exit(0)
  } catch (error) {
    console.error('❌ Health check failed:', error.message)
    process.exit(1)
  }
}

// Запуск если скрипт вызван напрямую
if (require.main === module) {
  main()
}

module.exports = { performHealthCheck }
