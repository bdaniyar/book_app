from sqladmin import ModelView
from app.models.user import User
from app.main import admin

from app.core.security import hash_password


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.username]

    form_columns = [
        User.email,
        User.username,
        User.first_name,
        User.last_name,
        User.bio,
        User.avatar_url,
        User.is_active,
        User.is_superuser,
        "password",
    ]


    async def on_model_change(self, data, model, is_created, request):
        # If password was provided in the form, hash it into hashed_password.
        password = data.get("password")
        if password:
            model.hashed_password = hash_password(password)


admin.add_view(UserAdmin)
