"""Вспомогательные функции"""


def delete_attachments(attachments, post_data):
    """Удаляет выбранные вложения из файлового 
    хранилища и базы данных."""
    for attachment in attachments:
        if post_data.get(f"delete_attachment_{attachment.pk}") == "1":
            attachment.file.delete(save=False)
            attachment.delete()
