// Not a usable file yet

// ---------------- For .db file management and storage ------------------
import 'package:http/http.dart' as http;
import 'dart:async';
import 'dart:typed_data';
import 'dart:io' as io;
import 'package:sqflite/sqflite.dart';
// import 'data_extraction.dart';  // This will conditionally import either the mobile or web version
// import 'data_extraction.dart';

// DatabaseFactory sqfliteDatabaseFactory = databaseFactorySqflitePlugin;

// Downloads the SQLite .db file from GitHub using its raw url
Future<Uint8List> downloadDatabaseFromGithub() async {
  String rawUrl = 'https://raw.githubusercontent.com/TuitionScheduler/curriculadora/curriculum-form/data/database/courses.db';
  http.Response response = await http.get(Uri.parse(rawUrl));
  
  if (response.statusCode == 200) {
    print('Successfully downloaded .db file from Github');
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
  print('Successfully stored database in device storage');
}


// Future<List<Map<String, dynamic>>> getAllRecordsFromDBMobile(String tableName) async {
//   String pathToDatabaseStorage = await getDatabasesPath();
//   Database database = await openDatabase('$pathToDatabaseStorage/courses.db');
//   // how to add a new element?
//   List<Map<String, dynamic>> result = await database.rawQuery('SELECT * FROM $tableName');
//   await database.close();
//   return result;
// }


// Future<List<Map<String, dynamic>>> getAllRecordsFromDBColumnMobile(String tableName, String columnName) async {
//   String pathToDatabaseStorage = await getDatabasesPath();
//   Database database = await openDatabase('$pathToDatabaseStorage/courses.db');
//   // how to add a new element?
//   List<Map<String, dynamic>> result = await database.rawQuery('SELECT $columnName FROM $tableName');
//   await database.close();
//   return result;
// }


// Future<List<Map<String, dynamic>>> getDataFromDBMobile(String tableName, String columnName, dynamic data) async {
//   String pathToDatabaseStorage = await getDatabasesPath();
//   Database database = await openDatabase('$pathToDatabaseStorage/courses.db');
//   List<Map<String, dynamic>> result = await database.rawQuery('SELECT * FROM $tableName WHERE $columnName = ?', [data]);
//   // how to add a new element?
//   await database.close();
//   return result;
// }


// Check if the database has already been downloaded and stored 
// in the device's "/Databases" directory
// For Android and IOS
void checkIfDatabaseStoredInDeviceStorage() async {
  String pathToDatabaseStorage = await getDatabasesPath();
  if (!(await io.File('$pathToDatabaseStorage/courses.db').exists())) {
    print('Database not previously stored in device storage. Downloading database into device storage...');
    Uint8List databaseBytes = await downloadDatabaseFromGithub();
    await storeDatabaseInDeviceStorage(databaseBytes);
  }
}

