from sqladmin import ModelView
from app.models.user import User
from app.main import admin


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.username]


admin.add_view(UserAdmin)
