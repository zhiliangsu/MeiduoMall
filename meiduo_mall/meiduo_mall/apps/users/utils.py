def jwt_response_payload_handler(token, user=None, request=None):
    """重写jwt登录认证方法的响应体"""
    return {
        'token': token,
        'username': user.username,
        'user_id': user.id,
    }
