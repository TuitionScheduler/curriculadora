// Not a usable file yet

// import 'dart:js_interop_unsafe';

//import 'dart:core' as core;

// ------------- For .db file management, storage and queries ------------------
import 'dart:async';
// Cannot import 'io' package because 'io' doesn't exist for web platforms
import 'dart:io' as io;
import 'dart:js_interop';
import 'dart:js_util';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
// import 'package:indexed_db/indexed_db.dart' as idb;
// package:indexed_db/indexed_db.dart';
// import 'package:web/web.dart' as web;
// import 'package:sqflite_common_ffi_web/sqflite_ffi_web.dart';
import 'package:idb_sqflite/idb_sqflite.dart' as idb_sql;
import 'package:sqflite/sqflite.dart';
import 'package:url_launcher/link.dart';

// import 'dart:io' show Platform;
import 'Platform_Checker/platform_is.dart';
import 'custom_sql_javascript_wrapper.dart';

// Downloads the SQLite .db file from GitHub using its raw url
Future<Uint8List> downloadDatabaseFromGithub() async {
  String rawUrl =
      'https://raw.githubusercontent.com/TuitionScheduler/curriculadora/curriculum-form/data/database/courses.db';
  http.Response response = await http.get(Uri.parse(rawUrl));

  if (response.statusCode == 200) {
    print('Successfully downloaded .db file from Github');
    return response.bodyBytes; // Return the raw bytes of the .db file
  } else {
    throw Exception('Could not download the .db file from Github');
  }
}

Future<void> storeDatabaseInDeviceStorage(Uint8List databaseBytes) async {
  String pathToDatabaseStorage = await getDatabasesPath();
  String dbFilePath = '$pathToDatabaseStorage/courses.db';
  io.File dbFile = io.File(
      dbFilePath); // specified io due to File Class ambiguity between io.File and web.File
  await dbFile.writeAsBytes(databaseBytes);
  print('Successfully stored database in device storage');
}

// Creates an Indexed Database that stores courses.db
// For web platforms (browsers)
Future<void> storeDatabaseInIndexedStorage(Uint8List databaseBytes) async {
  idb_sql.IdbFactory idbFactory =
      idb_sql.getIdbFactorySqflite(databaseFactorySqflitePlugin);

  // Creates an Indexed Database and a general ObjectStore to store files in
  idb_sql.Database indexedDatabase = await idbFactory.open(
    'User_Indexed_Storage',
    version: 1,
    onUpgradeNeeded: (idb_sql.VersionChangeEvent event) {
      idb_sql.Database database = event.database;
      database.createObjectStore('localFiles', autoIncrement: true);
      print('Indexed Database and Object Store created');
    },
  );

  // Stores courses.db in the created ObjectStore
  idb_sql.Transaction transaction =
      indexedDatabase.transaction('localFiles', 'readwrite');
  idb_sql.ObjectStore store = transaction.objectStore('localFiles');
  await store.put({databaseBytes: 'courses.db'});
  await transaction.completed;
  indexedDatabase.close;
  // do I need to close or not? Delete if this part causes issues
  print('Stored courses.db in Indexed Database');

  // Cannot use 'idb_sqflite' package that supports SQLite querying
  // for Indexed Databases (IDB) for web platforms because we would
  // need to populate the IDB with all the courses.db records all
  // over again. We would have to insert all the records and it
  // would take many minutes to process, which would not be an
  // acceptable processing time for the user.

  // Using non-deprecated 'indexed_db' package
  // Cannot be used because opening the Indexed Database (IDB)
  // requires a file path, but IDBs cannot be accessed through
  // a directory path.

  // // The one that worked, red line-wise :'''''''''(
  // idb.IdbFactory idbFactory = idb.IdbFactory();

  // idb.OpenCreateResult result = await idbFactory.openCreate("User_Indexed_Storage", "local_files");
  // idb.Database database = result.database;
  // idb.ObjectStore store = database.transaction('local_files', 'readwrite').objectStore('local_files');
  // // idb.ObjectStore store = transaction.objectStore('local_files');

  // JSAny databaseBytesJS = databaseBytes.toJS;
  // JSArray<JSAny> databaseBytesJSArray = JSArray();
  // databaseBytesJSArray.add(databaseBytesJS);
  // web.Blob databaseFile = web.Blob(databaseBytesJSArray); // ????

  // await store.put(databaseBytes, 'courses.db');
  // database.close();

  // Using the recommended 'web' package
  // Cannot be used because it is a new package with limited use
  // among users and limited documentation regarding the indexed_db
  // class, therefore syntax and logic is unclear.

  // web.IDBOpenDBRequest indexedStorageRequest = web.window.indexedDB.open("User_Indexed_Storage", 1);

  // indexedStorageRequest.onupgradeneeded = (event) => {
  // const db = event.target.result;

  // db.onerror = (event) => {
  //   note.appendChild(document.createElement("li")).textContent =
  //     "Error loading database.";
  //   };
  // };

  // EventHandler eventHandler = indexedStorageRequest.onupgradeneeded;
  // indexedStorageRequest.addEventListener("upgradeNeeded", (event));

  // indexedStorageRequest.addEventListener("upgradeneeded", (web.Event event) {
  //   var db = event.target.result;
  //   print("AHHHH")
  // });

  // onUpgrade(web.window.indexedDB.open("User_Indexed_Storage", 1));
  //   web. IDBDatabase temp = e.target.result as web.IDBDatabase;
  //   if (!temp.objectStoreNames.contains("local_files")) {
  //     temp.createObjectStore("local_files");a
  //   }
  //   // indexedStorage = temp
  // });

  // Using the deprecated 'html/indexed_db' package
  // Cannot be used because it is deprecated

  // web.IDBOpenDBRequest indexedStorage = web.window.indexedDB.open("User_Indexed_Storage", version: 1, onUpgradeNeeded: (e) {
  //   web. IDBDatabase temp = e.target.result as web.IDBDatabase;
  //   if (!temp.objectStoreNames.contains("local_files")) {
  //     temp.createObjectStore("local_files");
  //   }
  //   // indexedStorage = temp
  // });

  // Stores the database in the ObjectStore
  // web.IDBObjectStore store = indexedStorageRequest.transaction!.objectStore("local_files");
  // IDBObjectStore store = indexedStorage.transaction!("local_files", "readwrite").("local_files");

  // JSAny databaseBytesJS = databaseBytes.toJS;
  // JSArray<JSAny> databaseBytesJSArray = JSArray();
  // databaseBytesJSArray.add(databaseBytesJS);
  // web.Blob databaseFile = web.Blob(databaseBytesJSArray); // ????
  // store.put(databaseFile);
  // do i need to close???
}

// Opens the database and prepares it for queries
// For web platforms (browsers)
Future<SqlJsDatabase> getDatabaseForWeb() async {
  // Opens courses.db from the Indexed Database
  idb_sql.IdbFactory idbFactory =
      idb_sql.getIdbFactorySqflite(databaseFactorySqflitePlugin);
  idb_sql.Database indexedDatabase =
      await idbFactory.open('User_Indexed_Storage');
  idb_sql.Transaction transaction =
      indexedDatabase.transaction("localFiles", 'readonly');
  idb_sql.ObjectStore store = transaction.objectStore('localFiles');
  Uint8List databaseBytes = store.getObject("courses.db") as Uint8List;
  await transaction.completed;
  print('Opened Indexed Database for SQL setup');

  // Converts the Dart-IndexedDatabase into a Javascript-SQLDatabase for
  // Javascript SQL query processing at runtime

  JSAny? result = initSqlJs({
    'locateFile': (String file) => 'sql-wasm.wasm',
  }.jsify());

  SqlJs sqlJs = result as SqlJs;

  // final SqlJs sqlJs = (await promiseToFuture(initSqlJs(
  // js_util.jsify({
  //   'locateFile': allowInterop((String file) => 'sql-wasm.wasm'),
  // }),
  // ))) as SqlJs;

  // SqlJs sqlJs = await promiseToFuture(initSqlJs({
  //   'locateFile': (String file) => 'sql-wasm.wasm',
  // })) as SqlJs;

  print('Successfully converted database into sqlJsDatabase');
  return sqlJs.Database(databaseBytes.toJS);

  // Using the non-deprecated 'indexed_db' package

  // idb.IdbFactory idbFactory = idb.IdbFactory();
  // idb.Database indexedStorage = await idbFactory.open("User_Indexed_Storage");
  // idb.ObjectStore store = indexedStorage.transaction("local_files", 'readonly').objectStore('local_files');
  // idb.Request databaseFileRequest = store.getKey("courses.db");

  // Using the recommended 'web/indexed_db' package

  // web.IDBOpenDBRequest indexedStorageRequest = web.window.indexedDB.open("User_Indexed_Storage", 1);
  // web.IDBObjectStore store = indexedStorageRequest.transaction!.objectStore("local_files");
  // web.IDBRequest databaseFile = store.get("courses.db");
  // web.Blob databaseFile = store.get("courses.db");

  // // Sets up database factory for SQLite queries
  // if (databaseFile != null) {
  //   ArrayBuffer dbFileBytes = await databaseFile.arrayBuffer();
  //   Uint8List dbFileUint8List = Uint8List.view(dbFileBytes);

  //   // final fileBytes = await dbFile!.slice(0, dbFile.size).arrayBuffer();
  //   // final byteData = ByteData.sublistView(fileBytes as Uint8List);

  //   DatabaseFactory factory = databaseFactoryFfiWeb;
  //   Database database = factory.openDatabase(dbFileUint8List);
  //   // Database database = factory.openDatabaseFromBytes(dbFileUint8List);
  //   return database;
  // }
  // else {
  //   await database.close();
  //   throw Exception('No database found in IndexedStorage.');
  // }
}

// Future<void> queryDatabase(int course) async {
//     // Query the database
//     // Returns a list of maps of type String, Dynamic
//     var result = await db.rawQuery('SELECT * FROM courses');
//     print('Courses: $result');

//     await db.close();
//     else {
//     print('No database found in IndexedDB.');
//   }
// }

// Converts Javascript object into Dart Maps List
List<Map<String, dynamic>> convertIntoMapList(JSArray<JSAny?> queryResult) {
  final List<Map<String, dynamic>> resultList = [];

  // Convert JSArray to Dart List
  final resultSets = queryResult.toDart.cast<Object?>();

  if (resultSets.isEmpty) return [];

  final firstResultSet = resultSets.first as JSObject;

  final columns = getProperty(firstResultSet, 'columns') as JSArray;
  final values = getProperty(firstResultSet, 'values') as JSArray;

  final dartColumns = columns.toDart.cast<String>();

  final rows = values.toDart.cast<List<Object?>>();
  for (var row in rows) {
    final rowMap = <String, dynamic>{};
    for (int i = 0; i < dartColumns.length; i++) {
      rowMap[dartColumns[i]] = row[i];
    }
    resultList.add(rowMap);
  }

  return resultList;

  // if (queryResult.isEmpty) {
  //   print('List<Map> conversion - Query result is empty');
  //   return [];
  // }

  // final columns = List<String>.from(queryResult[0]['columns']);
  // final rows = List<List<dynamic>>.from(queryResult[0]['values']);

  // print('List<Map> conversion - Query result not empty');
  // return rows.map((row) {
  //   final Map<String, dynamic> map = {};
  //   for (int i = 0; i < columns.length; i++) {
  //     map[columns[i]] = row[i];
  //   }
  //   return map;
  // }).toList();
}

// Queries the database for all the data records within a specified table (with all their fields (columns))
Future<Object> getAllRecordsFromDB(String tableName) async {
  print('Getting all records from $tableName table...');
  List<Map<String, dynamic>> result = [];
  if (kIsWeb) {
    print('Identified web platform');
    SqlJsDatabase webDatabase = await getDatabaseForWeb();
    JSArray<JSAny?> jsResult = webDatabase.exec('SELECT * FROM $tableName');
    // List<dynamic> jsResult
    // List<dynamic> - JS-specific object
    result = convertIntoMapList(jsResult);
    webDatabase.close();
  } else if (PlatformIs.android || PlatformIs.iOS) {
    print('Identified mobile device');
    String pathToDatabaseStorage = await getDatabasesPath();
    Database database = await openDatabase('$pathToDatabaseStorage/courses.db');
    result = await database.rawQuery('SELECT * FROM $tableName');
    // how to add a new element?
    await database.close();
  }

  if (result.isNotEmpty) {
    print('Successfully retreived query result!');
    return result;
  } else {
    // print('Table $tableName not found in courses.db');
    throw Exception('Table $tableName not found in courses.db');
  }
}

// Queries the database for all the data records within a specified column
Future<List<Map<String, dynamic>>> getAllRecordsFromDBColumn(
    String tableName, String columnName) async {
  print('Getting all records from column $columnName in $tableName table...');
  List<Map<String, dynamic>> result = [];
  if (kIsWeb) {
    print('Identified web platform');
    SqlJsDatabase webDatabase = await getDatabaseForWeb();
    JSArray<JSAny?> jsResult =
        webDatabase.exec('SELECT $columnName FROM $tableName');
    // List<dynamic> jsResult
    // List<dynamic> - JS-specific object
    result = convertIntoMapList(jsResult);
    webDatabase.close();
  } else if (PlatformIs.android || PlatformIs.iOS) {
    print('Identified mobile device');
    String pathToDatabaseStorage = await getDatabasesPath();
    Database database = await openDatabase('$pathToDatabaseStorage/courses.db');
    result = await database.rawQuery('SELECT $columnName FROM $tableName');
    // how to add a new element?
    await database.close();
  }

  if (result.isNotEmpty) {
    print('Successfully retreived query result!');
    return result;
  } else {
    // print('Column $columnName not found in $tableName table');
    throw Exception('Column $columnName not found in $tableName table');
  }
}

// Queries the database for a specific data element
Future<List<Map<String, dynamic>>> getDataFromDB(
    String tableName, String columnName, dynamic data) async {
  print('Getting $columnName : $data from $tableName table...');
  List<Map<String, dynamic>> result = [];
  if (kIsWeb) {
    print('Identified web platform');
    if (data is String) {
      data =
          "'${data.replaceAll("'", "''")}'"; // Escapes the String's single quotes
    } else {
      data = data
          .toString(); // Still converts to String so that the exec() query can process it
    }
    SqlJsDatabase webDatabase = await getDatabaseForWeb();
    JSArray<JSAny?> jsResult =
        webDatabase.exec('SELECT * FROM $tableName WHERE $columnName = $data');
    // List<dynamic> jsResult
    // List<dynamic> - JS-specific object
    result = convertIntoMapList(jsResult);
    webDatabase.close();
  } else if (PlatformIs.android || PlatformIs.iOS) {
    print('Identified mobile device');
    String pathToDatabaseStorage = await getDatabasesPath();
    Database database = await openDatabase('$pathToDatabaseStorage/courses.db');
    result = await database
        .rawQuery('SELECT * FROM $tableName WHERE $columnName = ?', [data]);
    // how to add a new element?
    await database.close();
  }

  if (result.isNotEmpty) {
    print('Successfully retreived query result!');
    return result;
  } else {
    // print('$columnName : $data not found in $tableName table');
    throw Exception('$columnName : $data not found in $tableName table');
  }
}

class DataExtraction extends StatefulWidget {
  const DataExtraction({super.key});

  @override
  State<DataExtraction> createState() => _DataExtractionState();
}

class _DataExtractionState extends State<DataExtraction> {
  @override
  void initState() {
    super.initState();
    _setupPersistentStorage();
  }

  // Download the database and store it in persistent storage when the app starts
  Future<void> _setupPersistentStorage() async {
    print('Started initial database setup...');
    // Check if the device is a web platform (browser)
    if (kIsWeb) {
      print('Using web platform');
      // Check if the database has already been downloaded and stored in Indexed Storage
      try {
        // indexedStorage = window.indexedDB.open("User_Indexed_Storage", version: 1);
        idb_sql.IdbFactory idbFactory =
            idb_sql.getIdbFactorySqflite(databaseFactorySqflitePlugin);
        await idbFactory.open('User_Indexed_Storage');
      } catch (e) {
        print(
            'Indexed Database has not been previously created. Creating Indexed Database...');
        Uint8List databaseBytes = await downloadDatabaseFromGithub();
        await storeDatabaseInIndexedStorage(databaseBytes);
      }
    }
    // Check if the device is Android or IOS (mobile)
    else if (PlatformIs.android || PlatformIs.iOS) {
      print('Using mobile device');
      String pathToDatabaseStorage = await getDatabasesPath();
      if (!(await io.File('$pathToDatabaseStorage/courses.db').exists())) {
        print(
            'Database not previously stored in device storage. Downloading database into device storage...');
        Uint8List databaseBytes = await downloadDatabaseFromGithub();
        await storeDatabaseInDeviceStorage(databaseBytes);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          const Text(
            'This is the Update Progress - Data Extraction Page',
          ),
          const Text("(MOCKUP)"),
          const Text("Your current plan for the next semester is:\n"
              "Year: 2024, Term: Spring\n"
              "CIIC4151\n"
              "CIPO3011\n"
              "EDFU3012\n"
              "INME4045\n"
              "PSIC3002"),
          Link(
              uri: Uri.parse(
                  'https://matrical.site/?term=Spring&year=2024&courses=CIIC4151%2CCIPO3011%2CEDFU3012%2CINME4045%2CPSIC3002'), // hard-coded url
              target: LinkTarget.blank,
              builder: (context, followLink) => ElevatedButton(
                  onPressed: followLink,
                  child: const Text("Export to Matrical"))),
          const Divider(),
          Text("Is this still your plan?"),
          ElevatedButton(
              onPressed: () {},
              child: Text("Yes, continue with this semester")),
          SizedBox(
            height: 10,
          ),
          ElevatedButton(
              onPressed: () {}, child: Text("No, generate new sequence"))
        ],
      ),
    );
  }
}
