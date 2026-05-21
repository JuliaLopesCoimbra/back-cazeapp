"""
Gera um par de chaves VAPID para Web Push (notificações no dispositivo).
Uso: na raiz de back-n1, execute: python scripts/generate_vapid_keys.py

A chave privada é salva em vapid_private.pem (na raiz de back-n1).
Adicione no back-n1/.env as duas variáveis impressas abaixo.
O frontend obtém a chave pública pela API GET /notifications/vapid-public-key.
"""
import os
import sys

# raiz do projeto = pasta acima de scripts/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEM_PATH = os.path.join(ROOT, "vapid_private.pem")


def main():
    try:
        from py_vapid import Vapid
        from cryptography.hazmat.primitives import serialization
    except ImportError as e:
        print("Instale o pacote: pip install py-vapid")
        sys.exit(1)

    v = Vapid()
    v.generate_keys()

    # Chave pública em base64url (formato esperado pelo navegador)
    public_bytes = v.public_key.public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    import base64
    public_b64 = base64.urlsafe_b64encode(public_bytes).replace(b"=", b"").decode("utf-8")

    # Salva chave privada em PEM (pywebpush aceita path ou conteúdo PEM)
    with open(PEM_PATH, "wb") as f:
        f.write(v.private_pem())
    print("Chave privada salva em:", PEM_PATH)

    print()
    print("=" * 60)
    print("Adicione no back-n1/.env (ou use o path absoluto do .pem):")
    print("=" * 60)
    print()
    print("VAPID_PUBLIC_KEY=" + public_b64)
    # Path relativo à raiz do back (onde o uvicorn costuma rodar)
    print("VAPID_PRIVATE_KEY=" + os.path.abspath(PEM_PATH).replace("\\", "/"))
    print()
    print("Reinicie a API (uvicorn) depois de salvar o .env.")
    print("O frontend usa a chave pública via API (não precisa de variável no front).")


if __name__ == "__main__":
    main()
