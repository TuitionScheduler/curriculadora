// Not a usable file yet

// import 'dart:js_interop_unsafe';

import 'dart:async';
import 'dart:js_interop';
import 'dart:js_util';
// import 'package:web/helpers.dart';
// import 'dart:html' as html;
import 'dart:typed_data';

// ------------- For .db file management, storage and queries ------------------
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:idb_shim/idb_browser.dart' as idb_shim;
// import 'package:web/web.dart' as web;
import 'package:idb_sqflite/idb_sqflite.dart' as idb_sql;

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

// Creates an Indexed Database that stores courses.db
// For web platforms (browsers)
Future<void> storeDatabaseInIndexedStorage(Uint8List databaseBytes) async {
  idb_sql.IdbFactory idbFactory = idb_shim.idbFactoryBrowser;

  // Creates an Indexed Database and a general ObjectStore to store files in
  idb_sql.Database indexedDatabase = await idbFactory.open(
    'User_Indexed_Storage',
    version: 1,
    onUpgradeNeeded: (idb_sql.VersionChangeEvent event) {
      idb_sql.Database database = event.database;
      if (!database.objectStoreNames.contains('localFiles')) {
        print(
            'Indexed Database and Object Store not yet created. Creating IndexedDB and ObjectStore...');
        database.createObjectStore('localFiles', autoIncrement: true);
      } else {
        print('Indexed Database and Object Store already created');
      }
    },
  );

  // Stores courses.db in the created ObjectStore
  idb_sql.Transaction transaction =
      indexedDatabase.transaction('localFiles', 'readwrite');
  idb_sql.ObjectStore store = transaction.objectStore('localFiles');
  var dbFile = await store.getObject("courses.db");
  if (dbFile != null) {
    print('courses.db is already in Indexed Storage');
    // print(dbFile.toString());
  } else {
    // databaseBytes = await downloadDatabaseFromGithub();
    await store.put(databaseBytes, 'courses.db');
    print('Stored courses.db in Indexed Database');
  }
  await transaction.completed;
  indexedDatabase.close;
  // do I need to close or not? Delete if this part causes issues
  print('Finishing storing courses.db in Indexed Storage');

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
Future<Uint8List> getDatabaseForWeb() async {
  // Opens courses.db from the Indexed Database
  idb_sql.IdbFactory idbFactory = idb_shim.idbFactoryBrowser;
  idb_sql.Database indexedDatabase =
      await idbFactory.open('User_Indexed_Storage');
  idb_sql.Transaction transaction =
      indexedDatabase.transaction("localFiles", 'readonly');
  idb_sql.ObjectStore store = transaction.objectStore('localFiles');
  Uint8List databaseBytes = await store.getObject("courses.db") as Uint8List;
  await transaction.completed;
  print('Opened Indexed Database for SQL setup');

  return databaseBytes;

  // Converts the Dart-IndexedDatabase into a Javascript-SQLDatabase for
  // Javascript SQL query processing at runtime

  // JSAny? result = initSqlJs({
  //   'locateFile': (String file) => 'sql-wasm.wasm',
  // }.jsify());

  // SqlJs sqlJs = result as SqlJs;

  // print('Successfully converted database into sqlJsDatabase');
  // return sqlJs.Database(databaseBytes.toJS);

  // final config = jsify({
  // 'locateFile': (String file) => 'sql-wasm.wasm',
  // });

  // final SqlJs sqlJs = await promiseToFuture(initSqlJs(config));
  // print('Successfully converted database into sqlJsDatabase');
  // return sqlJs.Database(databaseBytes.toJS); // or pass a buffer if you have one

  // JSAny? result = initSqlJs({
  //   'locateFile': (String file) => 'sql-wasm.wasm',
  // }.jsify());

  // SqlJs sqlJs = result as SqlJs;

  // print('Successfully converted database into sqlJsDatabase');
  // return sqlJs.Database(databaseBytes.toJS);

  // final SqlJs sqlJs = (await promiseToFuture(initSqlJs(
  // js_util.jsify({
  //   'locateFile': allowInterop((String file) => 'sql-wasm.wasm'),
  // }),
  // ))) as SqlJs;

  // SqlJs sqlJs = await promiseToFuture(initSqlJs({
  //   'locateFile': (String file) => 'sql-wasm.wasm',
  // })) as SqlJs;

  // print('Successfully converted database into sqlJsDatabase');
  // return sqlJs.Database(databaseBytes);

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

Future<void> queryToBackend(Uint8List databaseBytes) async {
  Uri uri = Uri.parse('http://localhost:8000/upload');
  http.MultipartRequest request = http.MultipartRequest('POST', uri);

  // Add the byte data as a file
  request.files.add(
    http.MultipartFile.fromBytes(
      'dbFile', // form field name
      databaseBytes,
      filename: 'courses.db',
      contentType: MediaType('application', 'octet-stream'),
    ),
  );

  final response = await request.send();

  if (response.statusCode == 200) {
    print('Upload successful!');
  } else {
    print('Upload failed with status ${response.statusCode}');
  }
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
  if (queryResult.length == 0) {
    print("Web query result not converted because it is empty");
    return [];
  }

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

  print(
      "Successfully converted query result to type: List<Map<String, dynamic>>");
  return resultList;
}

// List<Map<String, dynamic>> convertIntoMapList(List<dynamic> queryResult){

//   if (queryResult.isEmpty) {
//     print('List<Map> conversion - Query result is empty');
//     return [];
//   }

//   final columns = List<String>.from(queryResult[0]['columns']);
//   final rows = List<List<dynamic>>.from(queryResult[0]['values']);

//   print('List<Map> conversion - Query result not empty');
//   return rows.map((row) {
//     final Map<String, dynamic> map = {};
//     for (int i = 0; i < columns.length; i++) {
//       map[columns[i]] = row[i];
//     }
//     return map;
//   }).toList();
// }


// Future<List<Map<String, dynamic>>> getAllRecordsFromDBWeb(String tableName) async {
//   print("Getting all data records from $tableName table...");
//   SqlJsDatabase webDatabase = await getDatabaseForWeb(); 
//   print("Starting query execution...");
//   // List<dynamic> jsResult = webDatabase.exec('SELECT * FROM $tableName');
//   JSArray<JSAny?> jsResult = webDatabase.exec('SELECT * FROM $tableName');
//   print("Finished query execution");
//   // List<dynamic> jsResult
//   // List<dynamic> - JS-specific object
//   webDatabase.close();
//   return convertIntoMapList(jsResult);
// }


// Future<List<Map<String, dynamic>>> getAllRecordsFromDBColumnWeb(String tableName, String columnName) async {
//   SqlJsDatabase webDatabase = await getDatabaseForWeb();
//   JSArray<JSAny?> jsResult = webDatabase.exec('SELECT $columnName FROM $tableName');
//   // List<dynamic> jsResult
//   // List<dynamic> - JS-specific object
//   webDatabase.close();
//   return convertIntoMapList(jsResult);
// }

// Future<List<Map<String, dynamic>>> getDataFromDBWeb(String tableName, String columnName, dynamic data) async {
//   if (data is String){
//     data = "'${data.replaceAll("'", "''")}'"; // Escapes the String's single quotes
//   }
//   else {
//     data = data.toString(); // Still converts to String so that the exec() query can process it
//   }
//   SqlJsDatabase webDatabase = await getDatabaseForWeb();
//   JSArray<JSAny?> jsResult = webDatabase.exec('SELECT * FROM $tableName WHERE $columnName = $data');
//   // List<dynamic> jsResult
//   // List<dynamic> - JS-specific object
//   webDatabase.close();
//   return convertIntoMapList(jsResult);
// }

// Check if the database has already been downloaded and stored in Indexed Storage
Future<void> checkIfDatabaseStoredInIndexedStorage() async {
  // try {
  //   // indexedStorage = window.indexedDB.open("User_Indexed_Storage", version: 1);
  //   idb_sql.IdbFactory idbFactory = idb_shim.idbFactoryBrowser;
  //   await idbFactory.open('User_Indexed_Storage');

  // } catch (e) {
  //   print('Indexed Database has not been previously created. Creating Indexed Database...');
  print(
      'Checking if courses.db has already been downloaded and stored in Indexed Storage...');
  Uint8List databaseBytes = await downloadDatabaseFromGithub();
  // Uint8List dummyDatabaseBytes = Uint8List.fromList([1, 0, 1, 0, 1, 0, 1]);
  await storeDatabaseInIndexedStorage(databaseBytes);
  // }
}
