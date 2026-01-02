# 📡 API Integration Guide

## Overview

Фронтенд приложение готов к интеграции с FastAPI backend. Все API endpoints определены и организованы в модульной структуре.

---

## 📁 Структура API файлов

```
frontend/lib/
├── api-config.ts      # Конфигурация и endpoints
├── api-client.ts      # HTTP клиент
├── api-services.ts    # Сервисные функции
└── books-data.ts      # Типы и mock данные

frontend/hooks/
└── use-api.ts         # React хуки для API
```

---

## 🔧 Конфигурация

### 1. Environment Variables

Создайте `.env.local`:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Disable telemetry
NEXT_TELEMETRY_DISABLED=1
```

### 2. API Base URL

По умолчанию: `http://localhost:8000`

Изменить можно в:
- `.env.local` → `NEXT_PUBLIC_API_URL`
- `lib/api-config.ts` → `API_BASE_URL`

---

## 📋 Доступные Endpoints

### Books API

```typescript
import { bookService } from '@/lib/api-services'

// Получить все книги
const books = await bookService.getAll({ page: 1, limit: 20 })

// Получить книгу по ID
const book = await bookService.getById('book-id')

// Поиск книг
const results = await bookService.search('query', { genre: 'Fiction' })

// Трендовые книги
const trending = await bookService.getTrending(10)

// Рекомендации
const recommended = await bookService.getRecommended(10)

// Книги по категории
const categoryBooks = await bookService.getByCategory('fiction')

// Похожие книги
const similar = await bookService.getSimilar('book-id', 4)
```

### Categories API

```typescript
import { categoryService } from '@/lib/api-services'

// Все категории
const categories = await categoryService.getAll()

// Категория по ID
const category = await categoryService.getById('category-id')
```

### Library API

```typescript
import { libraryService } from '@/lib/api-services'

// Вся библиотека
const library = await libraryService.getAll()

// Читаемые сейчас
const reading = await libraryService.getReading()

// Хочу прочитать
const wantToRead = await libraryService.getWantToRead()

// Избранное
const favorites = await libraryService.getFavorites()

// Добавить книгу
await libraryService.addBook('book-id', 'reading')

// Удалить книгу
await libraryService.removeBook('book-id')

// Обновить статус
await libraryService.updateStatus('book-id', 'read')
```

### Reviews API

```typescript
import { reviewService } from '@/lib/api-services'

// Отзывы для книги
const reviews = await reviewService.getByBookId('book-id')

// Создать отзыв
await reviewService.create('book-id', 5, 'Great book!')

// Обновить отзыв
await reviewService.update('review-id', 4, 'Updated review')

// Удалить отзыв
await reviewService.delete('review-id')
```

### Profile API

```typescript
import { profileService } from '@/lib/api-services'

// Получить профиль
const profile = await profileService.get()

// Обновить профиль
await profileService.update({ name: 'New Name', bio: 'Bio' })

// Статистика
const stats = await profileService.getStats()

// Активность чтения
const activity = await profileService.getReadingActivity()
```

### Recommendations API

```typescript
import { recommendationService } from '@/lib/api-services'

// Персональные рекомендации
const personalized = await recommendationService.getPersonalized(10)

// На основе книги
const basedOn = await recommendationService.getBasedOnBook('book-id')

// Популярные в жанре
const popular = await recommendationService.getPopularInGenre('Fiction')

// Новинки
const newReleases = await recommendationService.getNewReleases(10)
```

---

## ⚛️ React Hooks

### useApi - Для GET запросов

```typescript
import { useApi } from '@/hooks/use-api'
import { bookService } from '@/lib/api-services'

function BooksPage() {
  const { data, loading, error, refetch } = useApi(
    () => bookService.getAll(),
    [], // dependencies
    {
      enabled: true,
      onSuccess: (books) => console.log('Books loaded:', books),
      onError: (error) => console.error('Error:', error),
    }
  )

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error: {error}</div>
  if (!data) return <div>No data</div>

  return (
    <div>
      {data.map(book => <BookCard key={book.id} book={book} />)}
      <button onClick={refetch}>Refresh</button>
    </div>
  )
}
```

### useMutation - Для POST/PUT/DELETE

```typescript
import { useMutation } from '@/hooks/use-api'
import { reviewService } from '@/lib/api-services'

function ReviewForm({ bookId }) {
  const { mutate, loading, error } = useMutation(
    (data: { rating: number; text: string }) =>
      reviewService.create(bookId, data.rating, data.text),
    {
      onSuccess: (review) => {
        console.log('Review created:', review)
        // Refresh reviews list
      },
      onError: (error) => {
        console.error('Failed to create review:', error)
      },
    }
  )

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    mutate({ rating: 5, text: 'Great book!' })
  }

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <button type="submit" disabled={loading}>
        {loading ? 'Submitting...' : 'Submit Review'}
      </button>
      {error && <p className="text-red-500">{error}</p>}
    </form>
  )
}
```

### usePagination - Для пагинации

```typescript
import { usePagination } from '@/hooks/use-api'
import { bookService } from '@/lib/api-services'

function BooksList() {
  const {
    data,
    loading,
    error,
    page,
    limit,
    hasMore,
    nextPage,
    prevPage,
    goToPage,
  } = usePagination(
    (page, limit) => bookService.getAll({ page, limit }),
    1, // initial page
    20  // items per page
  )

  return (
    <div>
      {data?.map(book => <BookCard key={book.id} book={book} />)}
      
      <div className="pagination">
        <button onClick={prevPage} disabled={page === 1}>
          Previous
        </button>
        <span>Page {page}</span>
        <button onClick={nextPage} disabled={!hasMore}>
          Next
        </button>
      </div>
    </div>
  )
}
```

### useInfiniteScroll - Для бесконечной прокрутки

```typescript
import { useInfiniteScroll } from '@/hooks/use-api'
import { bookService } from '@/lib/api-services'

function InfiniteBooksList() {
  const { data, loading, hasMore, fetchMore } = useInfiniteScroll(
    (page, limit) => bookService.getAll({ page, limit }),
    20 // items per page
  )

  return (
    <div>
      {data.map(book => <BookCard key={book.id} book={book} />)}
      
      {hasMore && (
        <button onClick={fetchMore} disabled={loading}>
          {loading ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  )
}
```

---

## 🔄 Примеры использования в компонентах

### Страница с книгами

```typescript
'use client'

import { useApi } from '@/hooks/use-api'
import { bookService } from '@/lib/api-services'
import { BookCard } from '@/components/book-card'

export default function BooksPage() {
  const { data: books, loading, error } = useApi(
    () => bookService.getTrending(20)
  )

  if (loading) return <LoadingSkeleton />
  if (error) return <ErrorMessage message={error} />

  return (
    <div className="grid grid-cols-4 gap-6">
      {books?.map(book => (
        <BookCard key={book.id} book={book} />
      ))}
    </div>
  )
}
```

### Добавление в библиотеку

```typescript
'use client'

import { useMutation } from '@/hooks/use-api'
import { libraryService } from '@/lib/api-services'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'

export function AddToLibraryButton({ bookId }: { bookId: string }) {
  const { mutate, loading } = useMutation(
    (status: LibraryStatus) => libraryService.addBook(bookId, status),
    {
      onSuccess: () => {
        toast.success('Book added to library!')
      },
      onError: (error) => {
        toast.error(`Failed to add book: ${error}`)
      },
    }
  )

  return (
    <Button
      onClick={() => mutate('want-to-read')}
      disabled={loading}
    >
      {loading ? 'Adding...' : 'Add to Library'}
    </Button>
  )
}
```

---

## 🎯 API Endpoints Список

### Books
- `GET /api/v1/books` - Все книги
- `GET /api/v1/books/:id` - Книга по ID
- `GET /api/v1/books/search` - Поиск
- `GET /api/v1/books/trending` - Трендовые
- `GET /api/v1/books/recommended` - Рекомендованные
- `GET /api/v1/books/category/:category` - По категории
- `GET /api/v1/books/:id/similar` - Похожие

### Categories
- `GET /api/v1/categories` - Все категории
- `GET /api/v1/categories/:id` - Категория по ID

### Library
- `GET /api/v1/library` - Вся библиотека
- `GET /api/v1/library/reading` - Читаемые
- `GET /api/v1/library/want-to-read` - Хочу прочитать
- `GET /api/v1/library/favorites` - Избранное
- `POST /api/v1/library/add` - Добавить книгу
- `DELETE /api/v1/library/remove/:id` - Удалить книгу
- `PATCH /api/v1/library/update/:id` - Обновить статус

### Reviews
- `GET /api/v1/reviews/book/:bookId` - Отзывы книги
- `POST /api/v1/reviews` - Создать отзыв
- `PUT /api/v1/reviews/:id` - Обновить отзыв
- `DELETE /api/v1/reviews/:id` - Удалить отзыв

### Profile
- `GET /api/v1/profile` - Профиль
- `PUT /api/v1/profile` - Обновить профиль
- `GET /api/v1/profile/stats` - Статистика
- `GET /api/v1/profile/reading-activity` - Активность

### Recommendations
- `GET /api/v1/recommendations/personalized` - Персональные
- `GET /api/v1/recommendations/book/:id` - На основе книги
- `GET /api/v1/recommendations/genre/:genre` - По жанру
- `GET /api/v1/recommendations/new-releases` - Новинки

### Search
- `GET /api/v1/search/books` - Поиск книг
- `GET /api/v1/search/authors` - Поиск авторов
- `GET /api/v1/search/advanced` - Расширенный поиск

### Auth (будущее)
- `POST /api/v1/auth/login` - Вход
- `POST /api/v1/auth/register` - Регистрация
- `POST /api/v1/auth/logout` - Выход
- `GET /api/v1/auth/me` - Текущий пользователь

---

## 🚀 Следующие шаги

### Для подключения к реальному backend:

1. **Запустить backend**
   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn main:app --reload
   ```

2. **Обновить .env.local**
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Заменить mock данные на API calls**
   
   Вместо:
   ```typescript
   import { trendingBooks } from '@/lib/books-data'
   ```
   
   Использовать:
   ```typescript
   const { data: trendingBooks } = useApi(() => bookService.getTrending())
   ```

4. **Добавить обработку ошибок**
   ```typescript
   if (error) return <ErrorComponent error={error} />
   if (loading) return <LoadingSpinner />
   ```

---

## 📚 Типы данных

Все типы определены в:
- `lib/books-data.ts` - Book, Category
- `lib/api-services.ts` - Review, UserProfile, LibraryStatus

---

## ✅ Преимущества текущей реализации

- ✅ Централизованная конфигурация
- ✅ Type-safe API calls (TypeScript)
- ✅ Переиспользуемые сервисы
- ✅ React хуки для удобства
- ✅ Обработка ошибок
- ✅ Поддержка пагинации
- ✅ Поддержка infinite scroll
- ✅ Легко тестировать
- ✅ Готово к продакшену

---

**Статус**: ✅ API структура готова  
**Next**: Подключение к реальному backend
