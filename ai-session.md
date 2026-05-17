# Критичний аналіз unit-тестів PointsService


Набір із **28 тест-кейсів** (параметризація рівнів дає 8 окремих прогонів) організований у логічні класи (`TestAwardPoints`, `TestRedeemPoints` тощо), що відповідає підходу describe-блоків. Усі тести проходять; покриття `src/points_service.py` — **98%** (1 непокритий рядок — `RuntimeError` при некоректній конфігурації порогів рівнів).

Загальна оцінка: **добрий рівень для навчального/практичного проєкту**, з чіткою структурою та ізоляцією I/O. Для production-ready suite потрібні доопрацювання в частині суворості AAA, типів моків, негативних сценаріїв і стабільності тестового середовища.

| Критерій | Оцінка | Коментар |
|----------|--------|----------|
| Патерн AAA | 7/10 | Коментарі є, але є змішування Act/Assert і «порожній» Arrange |
| Ізоляція залежностей | 8/10 | MagicMock + фікстури; немає `spec`/fakes |
| Граничні випадки | 7/10 | Обов'язкові кейси покриті; є прогалини |
| Стабільність / підтримуваність | 7/10 | Дублювання Arrange; часткове перевикористання моків між тестами |

---

## 1. Дотримання патерну AAA (Arrange / Act / Assert)

### Сильні сторони

- У більшості тестів явно позначені секції `# Arrange`, `# Act`, `# Assert` (або `# Act / Assert` для exception-тестів).
- Happy-path сценарії (`test_award_points_success`, `test_redeem_points_success`, `test_get_balance_returns_repository_value`) мають **чітке трьохфазне розділення**: підготовка даних → виклик методу → перевірка результату та побічних ефектів.
- Assert-блоки перевіряють не лише return value, а й **взаємодію з колабораторами** (`assert_called_once_with`, `assert_not_called`), що відповідає best practice для unit-тестів сервісного шару.

### Відхилення та недоліки

| Проблема | Приклад | Рекомендація |
|----------|---------|--------------|
| **Злиття Act і Assert** | `test_award_points_unknown_action_raises`, `test_redeem_points_insufficient_balance_raises` — мітка `# Act / Assert` | Допустимо для exception-тестів, але для звіту краще: Act у `with pytest.raises`, Assert після блоку — перевірка, що репозиторій не викликався |
| **Формальний Arrange без змісту** | `test_get_level_by_points_thresholds`: коментар `# (parametrized inputs)` без реальної підготовки | Винести параметри в `@pytest.mark.parametrize` як єдине джерело даних; Arrange можна опустити або додати `given_points = points` для читабельності |
| **Неповний Assert у redeem** | `test_redeem_points_exact_balance_succeeds` — лише `assert_called_once()` без перевірки аргументів | Додати `assert_called_once_with("user-1", "redeem", -50, transaction_type="redeem")` |
| **Дублювання Act+Assert без окремого Act** | `test_award_points_triggers_achievement_callback` не перевіряє return value / `add_transaction` | Розширити Assert: переконатися, що транзакція записана до spy-перевірки |

### Висновок по AAA

Патерн **дотримано на рівні ~75–80% суворості**: структура видима, але не в кожному тесті три фази **семантично** розділені. Для академічного звіту з формулюванням «суворо в кожному тесті» — це **часткове виконання**: exception-тести та параметризовані кейси потребують уточнення або рефакторингу.

---

## 2. Ізоляція залежностей (Mock / Stub / Spy)

### Архітектура ізоляції

```
PointsService
    ├── PointsRepository   → MagicMock (conftest)
    ├── UserRepository     → MagicMock (conftest)
    └── AchievementService → MagicMock (conftest)
```

- **Фікстура `points_service`** інжектує три моки — тести не торкаються БД, мережі чи файлової системи. Це **справжні unit-тести**, не integration.
- **`return_value` / `side_effect`** використовуються як **stubs** (наприклад, `get_balance.side_effect = [100, 70]` моделює два читання балансу під час redeem).
- **Spy-патерн** реалізовано в `test_award_points_triggers_achievement_callback`: підміна `on_points_awarded` окремим `MagicMock()` і перевірка виклику.

### Сильні сторони

- Негативні сценарії перевіряють **відсутність побічних ефектів** (`add_transaction.assert_not_called()`, `get_history.assert_not_called()`).
- `test_get_balance_does_not_call_achievement_service` — коректна перевірка **меж відповідальності**: `get_balance` не повинен чіпати achievement-шар.
- `TestPointsServiceIntegrationWithMocks::test_service_uses_stubbed_repositories` демонструє збірку сервісу без conftest — корисно для ізольованого smoke unit-тесту.

### Недоліки та ризики

| Недолік | Наслідок | Покращення |
|---------|----------|------------|
| **`MagicMock` без `spec`** | Тест не впаде, якщо сервіс викличе неіснуючий метод репозиторію (typo у коді) | `MagicMock(spec=PointsRepository)` або `autospec=True` |
| **Немає `pytest.fixture(autouse=True)` для reset** | Моки створюються заново на тест (функціональні фікстури) — ОК, але при scope=`module` були б витоки стану | Залишити scope за замовчуванням (`function`) — зараз це правильно |
| **Підміна методу на mock** (`achievement_service.on_points_awarded = on_awarded`) | Може приховати регресію, якщо сервіс почне викликати інший метод | Використати `wraps=` або `mocker.spy()` (pytest-mock) |
| **Немає перевірки порядку викликів** | При зміні логіки (спочатку callback, потім транзакція) тести можуть залишатися зеленими | `mock.assert_has_calls([call(...), call(...)])` для критичних flow |
| **Залежність від реалізації, а не контракту** | Тести знають про `transaction_type="award"` — coupling до внутрішньої реалізації | Прийнятно для unit-рівня; для стабільності — константи або builder транзакцій |

### Висновок по ізоляції

Ізоляція **ефективна для швидких unit-тестів**: зовнішні системи відсутні, стан контролюється через stub. Рівень «enterprise» вимагав би **typed fakes** (in-memory репозиторій) або **mock з spec** для раннього виявлення порушень контракту.

---

## 3. Покриття граничних випадків (Edge Cases)

### Обов'язкові кейси з ТЗ — статус

| Edge case | Покриття | Тест(и) |
|-----------|----------|---------|
| Недостатній баланс при redeem | ✅ | `test_redeem_points_insufficient_balance_raises` |
| Від'ємна сума (award/redeem) | ✅ | `test_award_points_negative_amount_raises`, `test_redeem_points_negative_amount_raises` |
| Нульова сума | ✅ | `test_award_points_zero_amount_raises`, `test_redeem_points_zero_amount_raises` |
| Неіснуюча дія | ✅ | `test_award_points_unknown_action_raises` |
| Неіснуючий користувач | ✅ | award, redeem, balance, history |
| Границі рівнів (99/100, 499/500, 1999/2000) | ✅ | `@pytest.mark.parametrize` — 8 кейсів |
| Redeem на точну суму балансу | ✅ | `test_redeem_points_exact_balance_succeeds` |
| Невалідний limit історії (0) | ✅ | `test_get_points_history_invalid_limit_raises` |
| Від'ємні бали для рівня | ✅ | `test_get_level_by_points_negative_raises` |

### Прогалини (не покрито або слабо покрито)

1. **Від'ємний `limit` для історії** (`limit=-1`) — у сервісі спрацює `InvalidAmountError`, тесту немає.
2. **Порожній `user_id`** (`""`, `None`) — поведінка не зафіксована тестами.
3. **Порядок валідації при award з невалідною дією та неіснуючим user** — чи перевіряється user до action? (зараз user першим — тест на `invalid_action` при `exists=False` відсутній).
4. **`RuntimeError` при зламаних `LEVEL_THRESHOLDS`** — рядок 69 не покритий (98% coverage).
5. **Повторний виклик `exists` / `get_balance`** — redeem викликає `get_balance` двічі (через `_ensure_user_exists` + логіку); `side_effect=[100, 70]` не перевіряє кількість викликів `exists` (можливий over-mocking).
6. **Типи даних** — `amount` як float/string не тестується (якщо це вимога API — gap).
7. **Негативний amount у `award_points` при невалідній дії** — чи викликається `is_valid_action`? (зараз amount перевіряється раніше — ок, але немає тесту порядку).

### Матриця покриття методів

| Метод | Happy path | Negative | Interaction assert |
|-------|------------|----------|-------------------|
| `award_points` | ✅ | ✅ | ✅ |
| `redeem_points` | ✅ | ✅ | частково |
| `get_balance` | ✅ | ✅ | ✅ |
| `get_level_by_points` | ✅ (parametrize) | ✅ | N/A (без залежностей) |
| `get_points_history` | ✅ | частково | ✅ |

### Висновок по edge cases

Обов'язкові кейси з завдання **покриті достатньо для зарахування вимог**. Для звіту з позиції QA Lead варто зазначити: **покриття граничних значень сильне в домені балів/рівнів, слабше в домені вхідних параметрів API** (limit, user_id, типи).

---

## 4. Потенційні проблеми та рекомендації щодо стабільності

### 4.1. Дублювання та підтримуваність

- Повторюваний патерн `user_repository.exists.return_value = True` у ~15 тестах — ризик copy-paste помилок.
- **Рекомендація:** фікстура `active_user(user_repository)` або helper `def given_user_exists(mock, user_id="user-1")`.

### 4.2. Тести, близькі до дублікатів

- `test_award_points_success` і `test_award_points_triggers_achievement_callback` частково перетинаються (обидва перевіряють award flow).
- `test_service_uses_stubbed_repositories` дублює логіку success-тесту без conftest.
- **Рекомендація:** об'єднати або чітко розвести ролі: один — «контракт результату», другий — «побічні ефекти / spy».

### 4.3. Coupling до тексту повідомлень

- `match="Unknown action"`, `match="Insufficient balance"` — при зміні i18n/тексту тести впадуть без зміни логіки.
- **Рекомендація:** перевіряти тип винятку + `exc_info.value` за кодом помилки (якщо додати `error_code` у exceptions).

### 4.4. Відсутність pytest-mock / freeze time

- Немає тестів на ідемпотентність, race conditions (для unit — норма), але також немає **parametrize для різних `user_id`**.

### 4.5. Coverage vs якість

- `--cov=src` показує 91% по пакету, але **абстрактні класи** (`repositories.py`, `achievement_service.py`) не тестуються напряму — це очікувано.
- Рядок `raise RuntimeError` у `get_level_by_points` — **мертвий з точки зору поточних даних** (завжди є поріг `0`). Тест на misconfiguration підвищить надійність.

### 4.6. CI / запуск

- Рекомендована команда з README: `pytest --cov=src --cov-report=term-missing -v`
- Додати в CI: `--cov-fail-under=80` та окремо `--cov=src.points_service` для фокусу на цільовому модулі.

### 4.7. Пріоритетний backlog покращень

| Пріоритет | Покращення | Ефект |
|-----------|------------|-------|
| P1 | `MagicMock(spec=...)` для репозиторіїв | Раннє виявлення помилок API |
| P1 | Тест `get_points_history(..., limit=-1)` | Закриття edge gap |
| P2 | Helper-фікстури для Arrange | Менше дублювання, стабільніші тести |
| P2 | Повний Assert у `test_redeem_points_exact_balance_succeeds` | Сильніший контракт |
| P3 | In-memory fake `PointsRepository` для 1–2 integration-style unit | Перевірка реалістичного flow балансу |
| P3 | Тест на `RuntimeError` / monkeypatch `LEVEL_THRESHOLDS=[]` | 100% coverage критичної гілки |
| P3 | `pytest-mock` + `mocker.spy` замість ручної підміни | Чистіший spy-патерн |

---

## 5. Підсумкові висновки для звіту

**Що зроблено добре**

- 28 тестів, логічне групування класами, мінімум 20+ кейсів — вимога виконана.
- Залежності ізольовані; тести швидкі (~0.2 с), детерміновані.
- Ключові бізнес-правила (баланс, валідація суми, невідома дія, рівні) перевірені.
- Використано різні техніки mock/stub/spy, що відповідає навчальним вимогам.

**Що варто покращити для production-grade stability**

- Уніфікувати AAA (розділити Act/Assert навіть у exception-тестах у звіті/коді).
- Посилити контрактні перевірки моків (`spec`, повні `assert_called_with`).
- Закрити дрібні edge gaps (від'ємний limit, порожній user_id).
- Зменшити дублювання Arrange через фікстури-builders.
- Додати CI gate на coverage цільового модуля.

**Загальна рекомендація QA Lead:** набір придатний для **здачі практичної роботи та демонстрації компетенцій unit-тестування**. Перед використанням у реальному продукті — один ітерація рефакторингу (spec mocks + helpers + закриття прогалин з розділу 3) підніме оцінку стабільності до **9/10**.

---

## Додаток: метрики прогону

```text
Тестів зібрано: 28
Результат: 28 passed
Coverage (src/points_service.py): 98% (1 рядок не покритий — RuntimeError)
Coverage (пакет src): 91%
```

Команда перевірки:

```bash
pytest --cov=src --cov-report=term-missing -v
```
