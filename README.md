# Gamification — Points Service

Сервіс нарахування та списання балів (Gamification) з unit-тестами на `pytest`.

## Структура проєкту

```
practice4_1/
├── src/
│   ├── points_service.py      # бізнес-логіка PointsService
│   ├── repositories.py        # абстракції PointsRepository, UserRepository
│   ├── achievement_service.py # абстракція AchievementService
│   └── exceptions.py          # доменні винятки
├── tests/
│   ├── conftest.py            # фікстури та моки залежностей
│   └── test_points_service.py # unit-тести (AAA, класи-групи)
├── requirements.txt
└── pytest.ini
```

## Скріншот coverage звіту 
<img width="1224" height="520" alt="зображення" src="https://github.com/user-attachments/assets/dddf041e-e5ea-4696-b5d2-71115a094cfd" />


## Встановлення залежностей

```bash
pip install -r requirements.txt
```

## Запуск тестів із покриттям

З кореня проєкту (`practice4_1`):

```bash
pytest --cov=src --cov-report=term-missing -v
```

Очікуваний результат: усі тести пройдені, покриття модуля `src/points_service.py` не менше **80%**.

Перевірка лише порогу покриття (опційно):

```bash
pytest --cov=src --cov-fail-under=80 --cov-report=term-missing -v
```

## API PointsService

| Метод | Опис |
|--------|------|
| `award_points(user_id, action, amount)` | Нарахувати бали за дію |
| `redeem_points(user_id, amount)` | Списати бали (перевірка балансу) |
| `get_balance(user_id)` | Поточний баланс |
| `get_level_by_points(points)` | Рівень: Bronze / Silver / Gold / Platinum |
| `get_points_history(user_id, limit)` | Історія транзакцій |

### Пороги рівнів

| Рівень | Балів (від) |
|--------|-------------|
| Bronze | 0 |
| Silver | 100 |
| Gold | 500 |
| Platinum | 2000 |

## Залежності (для мокування в тестах)

- `PointsRepository` — баланс, транзакції, історія
- `UserRepository` — перевірка існування користувача
- `AchievementService` — валідність дії та callback після нарахування
