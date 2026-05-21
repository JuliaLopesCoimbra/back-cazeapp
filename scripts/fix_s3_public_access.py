"""
Script para tornar todos os arquivos do bucket S3 públicos (ACL public-read).

Este script atualiza o ACL de todos os objetos existentes no bucket para 'public-read',
resolvendo o erro ERR_BLOCKED_BY_ORB que ocorre quando as imagens não são acessíveis publicamente.

Uso:
    cd back-n1
    python scripts/fix_s3_public_access.py
"""

import sys
import os

# Adicionar o diretório raiz ao path para importar app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from botocore.exceptions import ClientError
from app.config.settings import settings

def fix_s3_public_access():
    """
    Atualiza o ACL de todos os objetos no bucket para 'public-read'.
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY,
        region_name=settings.AWS_REGION
    )
    
    bucket_name = settings.AWS_BUCKET
    
    print(f"Iniciando atualização de ACL para bucket: {bucket_name}")
    print("Isso pode levar alguns minutos dependendo do número de arquivos...\n")
    
    try:
        # Listar todos os objetos no bucket
        paginator = s3_client.get_paginator('list_objects_v2')
        total_updated = 0
        total_errors = 0
        
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                key = obj['Key']
                try:
                    # Atualizar ACL para public-read
                    s3_client.put_object_acl(
                        Bucket=bucket_name,
                        Key=key,
                        ACL='public-read'
                    )
                    total_updated += 1
                    if total_updated % 100 == 0:
                        print(f"Atualizados {total_updated} arquivos...")
                except ClientError as e:
                    print(f"Erro ao atualizar {key}: {str(e)}")
                    total_errors += 1
        
        print(f"\n✅ Concluído!")
        print(f"   - Arquivos atualizados: {total_updated}")
        if total_errors > 0:
            print(f"   - Erros: {total_errors}")
        
    except ClientError as e:
        print(f"❌ Erro ao acessar o bucket: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    fix_s3_public_access()

