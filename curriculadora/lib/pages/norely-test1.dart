// Not a usable file yet

import 'package:flutter/material.dart';
import 'package:url_launcher/link.dart';
// ------------- For .db file management, storage and queries ------------------
import 'dart:async';
import 'package:http/http.dart' as http;
import 'dart:typed_data';
import 'package:indexed_db/indexed_db.dart';
import 'package:sqflite_common_ffi/sqflite_ffi_web.dart';
import 'package:flutter/foundation.dart';
import 'dart:io';
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
  File dbFile = File(dbFilePath);
  await dbFile.writeAsBytes(databaseBytes);
}


// Creates an IndexedDB that stores courses.db 
// For web platforms (browsers)
Future<void> storeDatabaseInIndexedStorage(Uint8List databaseBytes) async {
  // Creates an IndexedDB and a general ObjectStore to store files in
  IDBDatabase indexedStorage = await window.indexedDB!.open("User_Indexed_Storage", version: 1, onUpgradeNeeded: (e) {
    temp = e.target.result as IDBDatabase;
    if (!temp.objectStoreNames.contains("local_files")) {
      temp.createObjectStore("local_files");
    }
    indexedStorage = temp
  });

  // Stores the database in the ObjectStore
  ObjectStore store = indexedStorage.transaction("local_files", "readwrite").objectStore("local_files");
  Blob databaseFile = Blob([databaseBytes]);
  await store.put(databaseFile, "courses.db");
  // do i need to close???
}


// Opens the database and configures setup for queries
Database querySetupForWeb() {
  IDBDatabase indexedStorage = await window.indexedDB.open("User_Indexed_Storage", version: 1);
  ObjectStore store = indexedStorage.transaction("local_files", "readonly").objectStore("local_files");
  Blob databaseFile = await store.get("courses.db");
  
  // Sets up database factory for SQLite queries
  if (databaseFile != null) {
    ArrayBuffer dbFileBytes = await databaseFile.arrayBuffer();
    Uint8List dbFileUint8List = Uint8List.view(dbFileBytes);

    // final fileBytes = await dbFile!.slice(0, dbFile.size).arrayBuffer();
    // final byteData = ByteData.sublistView(fileBytes as Uint8List);
    
    DatabaseFactoryFfiWeb factory = databaseFactoryFfiWeb;
    Database database = await factory.openDatabaseFromBytes(dbFileUint8List);
    return database;
  }
  else {
    await database.close();
    throw Exception('No database found in IndexedStorage.');
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


// Queries the database for all the data records within a specified table (with all their fields (columns))
List<Map<String, dynamic>> getAllRecordsFromDB(String table_name) async {
  if (kIsweb){
    Database database = querySetupForWeb();
  }
  else if (Platform.isAndroid OR Platform.isIOS) {
    String pathToDatabaseStorage = await getDatabasesPath();
    Database database = await openDatabase('$pathToDatabaseStorage/courses.db');
  }

  List<Map<String, dynamic>> result = await database.rawQuery('SELECT * FROM $table_name');
  await database.close();
  if (result.isNotEmpty) {
    return result;
  }
  else {
    print('Table $table_name not found in courses.db');
  }
}


// Queries the database for all the data records within a specified column 
List<Map<String, dynamic>> getAllRecordsFromDBColumn(String table_name, String column_name) async {
  if (kIsweb){
    Database database = querySetupForWeb();
  }
  else if (Platform.isAndroid OR Platform.isIOS) {
    String pathToDatabaseStorage = await getDatabasesPath();
    Database database = await openDatabase('$pathToDatabaseStorage/courses.db');
  }

  List<Map<String, dynamic>> result = await database.rawQuery('SELECT $column_name FROM $table_name');
  await database.close();
  if (result.isNotEmpty) {
      return result;
    }
  else {
    print('Column $column_name not found in $table_name table');
  }
}


// Queries the database for a specific data element 
List<Map<String, dynamic>> getDataFromDB(String table_name, String column_name, String data) async {
  if (kIsweb){
    Database database = querySetupForWeb();
  }
  
  else if (Platform.isAndroid OR Platform.isIOS) {
    String pathToDatabaseStorage = await getDatabasesPath();
    Database database = await openDatabase('$pathToDatabaseStorage/courses.db');
  }

  List<Map<String, dynamic>> result = await database.rawQuery(
    'SELECT * FROM $table_name 
    WHERE $column_name = ?', [data]);
  
  await database.close();
  if (result.isNotEmpty) {
    return result;
  }
  else {
    print('$column_name : $data not found in $table_name table');
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
    _setupLocalStorage();
  }

  // Download the database and store it in local storage when the app starts
  Future<void> _setupLocalStorage() async {
    // Check if the device is a web platform (browser) 
    if (kIsweb) {
      // Check if the database has already been downloaded and stored in IndexedStorage
      try {
        indexedStorage = window.indexedDB.open("User_Indexed_Storage", version: 1);
      } catch (e) {
        Uint8List databaseBytes = await downloadDatabaseFromGithub();
        await storeDatabaseInIndexedStorage(databaseBytes);
      }
    }
    // Check if the device is Android or IOS (mobile)
    else if (Platform.isAndroid OR Platform.isIOS){
      // Check if the database has already been downloaded and stored in the device's "/Databases" directory
      String pathToDatabaseStorage = await getDatabasesPath();
      if (!File('$pathToDatabaseStorage/courses.db').exists) {
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
