---
id: flutter-data-persistence
name: Flutter 数据持久化与离线优先规范
version: 1.0.0
platforms: [all]
tags: [storage, database, hive, drift, sqflite, isar, offline, sync, cache]
applies_when: 需求涉及本地存储、数据库、缓存、离线模式或数据同步
stage_hints: [spec, architecture, breakdown]
---

# Flutter 数据持久化与离线优先规范

> 直接依据:
> * Flutter 官方:**[docs.flutter.dev/cookbook/persistence](https://docs.flutter.dev/cookbook/persistence)**
> * Effective Dart:**[dart.dev/effective-dart](https://dart.dev/effective-dart)**
> * Offline-first 模式:**[web.dev/offline-cookbook](https://web.dev/offline-cookbook/)** (概念通用,Flutter 同样适用)

---

## 1. 存储方案选型

| 场景 | 推荐方案 | pub.dev | 维护方 |
|------|----------|---------|--------|
| 简单 K-V (用户偏好) | `shared_preferences` | [shared_preferences](https://pub.dev/packages/shared_preferences) | Flutter team |
| 安全 K-V (Token) | `flutter_secure_storage` | [flutter_secure_storage](https://pub.dev/packages/flutter_secure_storage) | 社区 |
| 文件 (JSON / 二进制) | `path_provider` + `dart:io` | [path_provider](https://pub.dev/packages/path_provider) | Flutter team |
| 关系型数据库 (SQL) | `drift` (类型安全) 或 `sqflite` (低层) | [drift](https://pub.dev/packages/drift), [sqflite](https://pub.dev/packages/sqflite) | Simon Binder / Flutter team |
| NoSQL 文档 | `hive_ce` 或 `isar_community` | [hive_ce](https://pub.dev/packages/hive_ce), [isar_community](https://pub.dev/packages/isar_community) | 社区 |
| 加密 SQLite | `sqflite_sqlcipher` | [sqflite_sqlcipher](https://pub.dev/packages/sqflite_sqlcipher) | 社区 |
| 大文件缓存 | `flutter_cache_manager` | [flutter_cache_manager](https://pub.dev/packages/flutter_cache_manager) | 社区 |

> **注意**: 原版 `hive` 和 `isar` 自 2024 年起已停止维护;社区分支 `hive_ce` (community edition) 和 `isar_community` 是其继承者。验证最新状态请查阅 pub.dev。

---

## 2. 选型决策树

```
需要存储什么?
├── 单个值 (主题、token) → shared_preferences / flutter_secure_storage
├── 几十~几百条记录,无关系 → hive_ce / isar_community
├── 复杂表关系、查询、迁移 → drift (推荐) 或 sqflite
└── 大量二进制 (图片、音视频) → 文件系统 (path_provider) + 索引表
```

| 维度 | drift | sqflite | hive_ce | isar_community |
|------|-------|---------|---------|---------------|
| 类型安全 | ✅ 编译期 | ❌ 字符串 SQL | ✅ 泛型 | ✅ 泛型 |
| 迁移工具 | ✅ 内置 | ⚠️ 手动 | ⚠️ 手动 | ⚠️ 手动 |
| 异步 API | ✅ | ✅ | ✅ | ✅ |
| Web 支持 | ✅ (sqlite3.wasm) | ❌ | ✅ | ✅ |
| 桌面支持 | ✅ | ✅ | ✅ | ✅ |
| 学习曲线 | 中 | 低 | 低 | 中 |

---

## 3. drift 标准用法

```dart
// schema.dart
import 'package:drift/drift.dart';

class Todos extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get title => text().withLength(min: 1, max: 200)();
  BoolColumn get done => boolean().withDefault(const Constant(false))();
  DateTimeColumn get createdAt => dateTime().clientDefault(() => DateTime.now())();
}

@DriftDatabase(tables: [Todos])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 1;

  @override
  MigrationStrategy get migration => MigrationStrategy(
    onCreate: (m) => m.createAll(),
    onUpgrade: (m, from, to) async {
      // 显式迁移每个版本
    },
  );
}
```

```bash
# 代码生成
dart run build_runner build --delete-conflicting-outputs
```

```dart
// 使用
final db = AppDatabase();
final todos = await db.select(db.todos).get();
await db.into(db.todos).insert(TodosCompanion.insert(title: 'Buy milk'));
```

---

## 4. shared_preferences 用法

```dart
final prefs = await SharedPreferences.getInstance();
await prefs.setString('user_name', 'Alice');
final name = prefs.getString('user_name'); // 'Alice'
```

**规则:**
1. **不要**用于敏感信息 (token、密码) → 用 `flutter_secure_storage`
2. **不要**用于复杂结构 → 用数据库
3. iOS 后存于 `NSUserDefaults`,Android 后存于 `SharedPreferences`,**未加密**

---

## 5. flutter_secure_storage 用法

```dart
const storage = FlutterSecureStorage(
  aOptions: AndroidOptions(encryptedSharedPreferences: true),
  iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
);
await storage.write(key: 'auth_token', value: token);
final token = await storage.read(key: 'auth_token');
```

| 平台 | 底层 |
|------|------|
| Android | EncryptedSharedPreferences (AES-256-GCM) |
| iOS / macOS | Keychain |
| Linux | libsecret |
| Windows | Credential Manager |
| Web | LocalStorage (**不安全**, 仅 dev 用) |

---

## 6. 离线优先 (Offline-first) 模式

### 6.1 经典三层架构

```
┌─────────────┐
│ UI / Widget │
└──────┬──────┘
       │
┌──────▼─────────────┐
│ Repository         │  ← 总是先读本地, 后台异步刷新
│  (combines local + remote) │
└──┬──────────────┬──┘
   │              │
┌──▼──┐         ┌─▼────────┐
│ DB  │         │ HTTP API │
└─────┘         └──────────┘
```

### 6.2 Repository 模板

```dart
class TodoRepository {
  final AppDatabase _db;
  final TodoApi _api;

  Stream<List<Todo>> watchAll() async* {
    // 1. 立即返回本地数据
    yield* _db.select(_db.todos).watch();
    // 2. 后台刷新
    unawaited(_refresh());
  }

  Future<void> _refresh() async {
    try {
      final remote = await _api.fetchAll();
      await _db.batch((batch) {
        batch.insertAllOnConflictUpdate(_db.todos, remote);
      });
    } catch (_) {
      // 离线时静默失败, UI 已展示本地数据
    }
  }

  Future<void> add(String title) async {
    final id = await _db.into(_db.todos).insert(...);
    try {
      await _api.create(title);
    } catch (_) {
      await _markPendingSync(id);  // 待联网重试
    }
  }
}
```

### 6.3 同步状态字段

```dart
// 在表里加 sync_status 列, 配合后台 worker 上传
class Todos extends Table {
  // ...
  IntColumn get syncStatus => intEnum<SyncStatus>().withDefault(const Constant(0))();
}

enum SyncStatus { synced, pendingCreate, pendingUpdate, pendingDelete }
```

---

## 7. 数据迁移最佳实践

1. **每次 schema 变更必须 bump `schemaVersion`**;不允许直接改老表结构。
2. **写显式 migration 而非 dropAllTables**;否则用户数据丢失。
3. **migration 函数必须幂等**(用户可能从 v1→v3 跳跃)。
4. **每次发布前在测试设备上测试 migration**(可用 `drift_dev` 工具生成 schema dump)。

```dart
MigrationStrategy get migration => MigrationStrategy(
  onCreate: (m) => m.createAll(),
  onUpgrade: (m, from, to) async {
    if (from < 2) {
      await m.addColumn(todos, todos.priority);
    }
    if (from < 3) {
      await m.createTable(tags);
    }
  },
);
```

---

## 8. 测试

```dart
test('TodoRepository returns cached data when offline', () async {
  final db = AppDatabase.memory();  // drift 内存数据库
  await db.into(db.todos).insert(TodosCompanion.insert(title: 'cached'));

  final api = MockTodoApi();
  when(() => api.fetchAll()).thenThrow(SocketException('offline'));

  final repo = TodoRepository(db: db, api: api);
  final todos = await repo.watchAll().first;
  expect(todos, hasLength(1));
  expect(todos.first.title, 'cached');
});
```

---

## 9. 反模式

| ❌ 反模式 | ✅ 正确做法 |
|----------|-------------|
| 在 UI 层直接调用数据库 | UI → Repository → DB |
| `shared_preferences` 存 JSON 字符串当数据库用 | 用真正的数据库 |
| 用 `path_provider.getTemporaryDirectory` 存重要数据 | iOS 临时目录会被系统清理;用 `getApplicationDocumentsDirectory()` |
| 启动时同步加载所有数据 | 用 `Stream` 增量加载 + 分页 |
| 没有迁移策略, 直接 dropAllTables | 用 `schemaVersion` + 显式 migration |

---

## 参考

- Flutter 官方 Persistence cookbook: <https://docs.flutter.dev/cookbook/persistence>
- shared_preferences: <https://pub.dev/packages/shared_preferences>
- flutter_secure_storage: <https://pub.dev/packages/flutter_secure_storage>
- path_provider: <https://pub.dev/packages/path_provider>
- drift (官方推荐 SQL): <https://drift.simonbinder.eu>
- drift package: <https://pub.dev/packages/drift>
- sqflite: <https://pub.dev/packages/sqflite>
- hive_ce (community fork): <https://pub.dev/packages/hive_ce>
- isar_community: <https://pub.dev/packages/isar_community>
- sqflite_sqlcipher: <https://pub.dev/packages/sqflite_sqlcipher>
- flutter_cache_manager: <https://pub.dev/packages/flutter_cache_manager>
- Offline cookbook (Google web.dev): <https://web.dev/offline-cookbook/>
- Repository pattern: <https://martinfowler.com/eaaCatalog/repository.html>

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **按数据形态选存储**:KV(prefs)/敏感(secure)/关系型(drift/sqflite)各有其位。
- **离线优先把本地当真相源**:UI 读本地,网络只负责同步。
- **Schema 会演化**:迁移是一等公民,从第一版就规划版本与升级路径。

**诚实边界:**

- 不替你做数据建模与冲突合并策略(那依业务语义)。
- 加密存储依赖平台 keystore/keychain,安全性以平台为准。
