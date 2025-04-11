class Settings:
    class Secure:
        ip = "94.159.102.219"
        method = "aes-256-cfb"
        protocol = "origin"
        obfs = "http_simple"

        API_KEY = '8025482746:AAHINGINXeVDqr3b2Qw0EsZk6J_QIvfPQso'

        admin_id = 967075635

    class Db:
        url = '/usr/bot/users.db'
        #url = 'ssrbot.db'

    class Global:
        log_file = 'logout.txt'
        common_out = 'nohup.out'

        qr_path = 'qrcode'


settings = Settings()