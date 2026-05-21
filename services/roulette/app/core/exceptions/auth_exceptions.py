from fastapi import HTTPException, status


def Unauthorized(detail="Não autorizado"):
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
