// Not a usable file yet

// import 'dart:js_interop_unsafe';

import 'package:flutter/material.dart';
import 'package:url_launcher/link.dart';
// ------------- For .db file management, storage and queries ------------------
import 'dart:async';
import 'package:http/http.dart' as http;
// import 'package:web/helpers.dart';
// import 'dart:html' as html;
import 'dart:typed_data';
import 'dart:js_interop';
import 'dart:js_util';
import 'custom_sql_javascript_wrapper.dart';
// import 'package:indexed_db/indexed_db.dart' as idb;
// package:indexed_db/indexed_db.dart'
// import 'package:web/web.dart' as web;
// import 'package:sqflite_common_ffi_web/sqflite_ffi_web.dart';
import 'package:idb_sqflite/idb_sqflite.dart' as idb_sql;
import 'package:flutter/foundation.dart';
import 'dart:io' as io;
import 'dart:io' show Platform;
import 'package:sqflite/sqflite.dart';

// Downloads the SQLite .db file from GitHub using its raw url
Future<Uint8List> downloadDatabaseFromGithub() async {
  String rawUrl = 'https://raw.githubusercontent.com/TuitionScheduler/curriculadora/curriculum-form/data/database/courses.db';
  http.Response response = await http.get(Uri.parse(rawUrl));
  
  if (response.statusCode == 200) {
    return response.bodyBytes; // Return the raw bytes of the .db file
  } else {
    throw Exception('Could not download the .db file from Github');
  }
}


// Stores courses.db in the device's "\Databases" directory
// For Android and IOS 
Future<void> storeDatabaseInDeviceStorage(Uint8List databaseBytes) async {
  String pathToDatabaseStorage = await getDatabasesPath();
  String dbFilePath = '$pathToDatabaseStorage/courses.db';
  io.File dbFile = io.File(dbFilePath); // specified io due to File Class ambiguity between io.File and web.File 
  await dbFile.writeAsBytes(databaseBytes);
}


// Creates an Indexed Database that stores courses.db 
// For web platforms (browsers)
Future<void> storeDatabaseInIndexedStorage(Uint8List databaseBytes) async {
  idb_sql.IdbFactory idbFactory = idb_sql.getIdbFactorySqflite(databaseFactorySqflitePlugin);
  
  // Creates an Indexed Database and a general ObjectStore to store files in
  idb_sql.Database indexedDatabase = await idbFactory.open(
    'User_Indexed_Storage',
    version: 1,
    onUpgradeNeeded: (idb_sql.VersionChangeEvent event) {
      idb_sql.Database database = event.database;
      database.createObjectStore('localFiles', autoIncrement: true);
    },
  );

  // Stores courses.db in the created ObjectStore
  idb_sql.Transaction transaction = indexedDatabase.transaction('localFiles', 'readwrite');
  idb_sql.ObjectStore store = transaction.objectStore('localFiles');
  await store.put({databaseBytes: 'courses.db'});
  await transaction.completed;
  indexedDatabase.close; 
  // do I need to close or not? Delete if this part causes issues








  
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
  idb_sql.IdbFactory idbFactory = idb_sql.getIdbFactorySqflite(databaseFactorySqflitePlugin);
  idb_sql.Database indexedDatabase = await idbFactory.open('User_Indexed_Storage');
  idb_sql.Transaction transaction = indexedDatabase.transaction("localFiles", 'readonly');
  idb_sql.ObjectStore store = transaction.objectStore('localFiles');
  Uint8List databaseBytes = store.getObject("courses.db") as Uint8List;
  await transaction.completed;

  // Converts the Dart-IndexedDatabase into a Javascript-SQLDatabase for 
  // Javascript SQL query processing at runtime
  SqlJs sqlJs = await promiseToFuture(initSqlJs({
    'locateFile': (String file) => 'sql-wasm.wasm',
  })) as SqlJs;

  return sqlJs.Database(databaseBytes);
  

  



  

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
List<Map<String, dynamic>> convertIntoMapList(List<dynamic> queryResult){
  if (queryResult.isEmpty) return [];

  final columns = List<String>.from(queryResult[0]['columns']);
  final rows = List<List<dynamic>>.from(queryResult[0]['values']);

  return rows.map((row) {
    final Map<String, dynamic> map = {};
    for (int i = 0; i < columns.length; i++) {
      map[columns[i]] = row[i];
    }
    return map;
  }).toList();
}


// Queries the database for all the data records within a specified table (with all their fields (columns))
Future<Object> getAllRecordsFromDB(String tableName) async {
  List<Map<String, dynamic>> result = [];
  if (kIsWeb){
    SqlJsDatabase webDatabase = await getDatabaseForWeb(); 
    List<dynamic> jsResult = webDatabase.exec('SELECT * FROM $tableName');
    // List<dynamic> - JS-specific object
    result = convertIntoMapList(jsResult);
    webDatabase.close();
  }
  else if (Platform.isAndroid || Platform.isIOS) {
    String pathToDatabaseStorage = await getDatabasesPath();
    Database database = await openDatabase('$pathToDatabaseStorage/courses.db');
    result = await database.rawQuery('SELECT * FROM $tableName');
    // how to add a new element?
    await database.close();
  }

  if (result.isNotEmpty) {
      return result;
  }
  else {
    // print('Table $tableName not found in courses.db');
    throw Exception('Table $tableName not found in courses.db'); 
  }
}


// Queries the database for all the data records within a specified column 
Future<List<Map<String, dynamic>>> getAllRecordsFromDBColumn(String tableName, String columnName) async {
  List<Map<String, dynamic>> result = [];
  if (kIsWeb){
    SqlJsDatabase webDatabase = await getDatabaseForWeb(); 
    List<dynamic> jsResult = webDatabase.exec('SELECT $columnName FROM $tableName');
    // List<dynamic> - JS-specific object
    result = convertIntoMapList(jsResult);
    webDatabase.close();
  }
  else if (Platform.isAndroid || Platform.isIOS) {
    String pathToDatabaseStorage = await getDatabasesPath();
    Database database = await openDatabase('$pathToDatabaseStorage/courses.db');
    result = await database.rawQuery('SELECT $columnName FROM $tableName');
    // how to add a new element?
    await database.close();
  }

  if (result.isNotEmpty) {
      return result;
  }
  else {
    // print('Column $columnName not found in $tableName table');
    throw Exception('Column $columnName not found in $tableName table'); 
  }
}


// Queries the database for a specific data element 
Future<List<Map<String, dynamic>>> getDataFromDB(String tableName, String columnName, dynamic data) async {
  List<Map<String, dynamic>> result = [];
  if (kIsWeb) {
    if (data is String){
      data = "'${data.replaceAll("'", "''")}'"; // Escapes the String's single quotes
    }
    else {
      data = data.toString(); // Still converts to String so that the exec() query can process it
    }
    SqlJsDatabase webDatabase = await getDatabaseForWeb(); 
    List<dynamic> jsResult = webDatabase.exec('SELECT * FROM $tableName WHERE $columnName = $data');
    // List<dynamic> - JS-specific object
    result = convertIntoMapList(jsResult);
    webDatabase.close();
  }
  else if (Platform.isAndroid || Platform.isIOS) {
    String pathToDatabaseStorage = await getDatabasesPath();
    Database database = await openDatabase('$pathToDatabaseStorage/courses.db');
    result = await database.rawQuery('SELECT * FROM $tableName WHERE $columnName = ?', [data]);
    // how to add a new element?
    await database.close();
  }

  if (result.isNotEmpty) {
      return result;
  }
  else {
    // print('$columnName : $data not found in $tableName table');
    throw Exception('$columnName : $data not found in $tableName table'); 
  }
}


class UpdateProgress extends StatefulWidget {
  const UpdateProgress({super.key});

  @override
  State<UpdateProgress> createState() => _UpdateProgressState();
}

class _UpdateProgressState extends State<UpdateProgress> {
  @override
  void initState() {
    super.initState();
    _setupPersistentStorage();
  }


  // Download the database and store it in persistent storage when the app starts
  Future<void> _setupPersistentStorage() async {
    // Check if the device is a web platform (browser) 
    if (kIsWeb) {
      // Check if the database has already been downloaded and stored in Indexed Storage
      try {
        // indexedStorage = window.indexedDB.open("User_Indexed_Storage", version: 1);
        idb_sql.IdbFactory idbFactory = idb_sql.getIdbFactorySqflite(databaseFactorySqflitePlugin);
        await idbFactory.open('User_Indexed_Storage');

      } catch (e) {
        Uint8List databaseBytes = await downloadDatabaseFromGithub();
        await storeDatabaseInIndexedStorage(databaseBytes);
      }
    }
    // Check if the device is Android or IOS (mobile)
    else if (Platform.isAndroid || Platform.isIOS){
      // Check if the database has already been downloaded and stored in the device's "/Databases" directory
      String pathToDatabaseStorage = await getDatabasesPath();
      if (!(await io.File('$pathToDatabaseStorage/courses.db').exists())) {
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
            'This is the Update Progress Page',
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
