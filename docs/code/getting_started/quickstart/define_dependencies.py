class EmailService:
    pass


class UserService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service
