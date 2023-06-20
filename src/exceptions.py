class CreateError(Exception):
    pass


class UpdateError(Exception):
    pass


class DeleteError(Exception):
    pass


class GetError(Exception):
    pass


class DuplicateEmailError(Exception):
    pass


class SendEmailError(Exception):
    pass


class MaxTasksReachedError(Exception):
    pass


class NoCompleteTasksError(Exception):
    pass
