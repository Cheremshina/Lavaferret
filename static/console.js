$(document).ready(function() {
    // Функция обновления логов
    function fetchLogs() {
        $.get('/server/' + serverId + '/api/logs', function(data) {
            $('#console-output').text(data.logs);
            // Прокрутка вниз
            var consoleDiv = document.getElementById('console-output');
            consoleDiv.scrollTop = consoleDiv.scrollHeight;
        }).fail(function() {
            $('#console-output').text('Failed to fetch logs');
        });
    }

    // Отправка команды
    $('#send-command').click(function() {
        var cmd = $('#command-input').val();
        if (!cmd) return;
        $.ajax({
            url: '/server/' + serverId + '/api/command',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({command: cmd}),
            success: function() {
                $('#command-input').val('');
                // После отправки обновляем логи с задержкой
                setTimeout(fetchLogs, 500);
            },
            error: function() {
                alert('Error sending command');
            }
        });
    });

    // Автообновление каждые 3 секунды
    setInterval(fetchLogs, 3000);
    // Первый раз сразу
    fetchLogs();


});