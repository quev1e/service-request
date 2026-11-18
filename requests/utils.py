def delete_attachments(attachments, post_data):
    for attachment in attachments:
        if post_data.get(f"delete_attachment_{attachment.pk}") == "1":
            attachment.file.delete(save=False)
            attachment.delete()