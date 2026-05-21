import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "n1appservicos@gmail.com"
SMTP_PASS = "qyem qrpo lgmk ilxs"
MAIL_FROM = "n1appservicos@gmail.com"

destinatarios = [
    "fernandoasfilho74@gmail.com",
    "fernandoal75.fa@gmail.com",
    "techpicbrand@gmail.com",
    "juliacristinalopes2607@gmail.com",
    "techservicos26@gmail.com"
]

def enviar_teste():
    try:
        print(f"--- Iniciando Conexão com {SMTP_HOST} ---")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
        server.set_debuglevel(1)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        
        for email in destinatarios:
            print(f"\n>> Tentando enviar para: {email}")
            msg = MIMEMultipart()
            msg['From'] = MAIL_FROM
            msg['To'] = email
            msg['Subject'] = "Teste Real N1 App - Verificacao"
            corpo = f"Teste de entrega para {email}\nEnvio realizado as {time.ctime()}"
            msg.attach(MIMEText(corpo, 'plain'))
            
            server.send_message(msg)
            print(f"RESULTADO: Servidor aceitou (250 OK) para {email}")
            time.sleep(1)
            
        server.quit()
        print("\n--- Teste Finalizado com Sucesso ---")
    except Exception as e:
        print(f"\nERRO NO SERVIDOR: {e}")

if __name__ == '__main__':
    enviar_teste()
