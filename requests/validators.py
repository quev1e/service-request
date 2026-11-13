from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

ALLOWED_EXTENSIONS = [
    "jpg", "jpeg", "png", "webp",
    "mp4", "mov", "webm",
]

def validate_file_size(file):
    max_size_mb = 10

    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(
            f"Файл слишком большой. Максимум — {max_size_mb} МБ."
        )


attachment_validators = [
    FileExtensionValidator(
        allowed_extensions=ALLOWED_EXTENSIONS,
        message="Можно загружать только фото или видео.",
    ),
    validate_file_size,
]