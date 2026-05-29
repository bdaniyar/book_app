from sqladmin import ModelView
from app.models.author import Author
from app.models.book import Book
from app.models.genre import Genre
from app.models.review import Review
from app.models.user import User
from app.models.user_book import UserBook
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


class AuthorAdmin(ModelView, model=Author):
    column_list = [Author.id, Author.name]


class GenreAdmin(ModelView, model=Genre):
    column_list = [Genre.id, Genre.name]


class BookAdmin(ModelView, model=Book):
    column_list = [Book.id, Book.title, Book.author_id, Book.average_rating, Book.review_count]


class ReviewAdmin(ModelView, model=Review):
    column_list = [Review.id, Review.book_id, Review.user_id, Review.rating]


class UserBookAdmin(ModelView, model=UserBook):
    column_list = [UserBook.id, UserBook.user_id, UserBook.book_id, UserBook.status]


admin.add_view(AuthorAdmin)
admin.add_view(GenreAdmin)
admin.add_view(BookAdmin)
admin.add_view(ReviewAdmin)
admin.add_view(UserBookAdmin)
