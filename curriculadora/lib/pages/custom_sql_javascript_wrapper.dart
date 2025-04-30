@JS()
library sqljs;

import 'dart:typed_data';
import 'dart:js_interop';

@JS('initSqlJs')
external JSAny initSqlJs([JSAny? config]);

@JS()
@staticInterop
class SqlJs {}

extension SqlJsExtension on SqlJs {
  external SqlJsDatabase Database([JSUint8Array? buffer]);
}

@JS()
@staticInterop
class SqlJsDatabase {}

extension SqlJsDatabaseExtension on SqlJsDatabase {
  external JSArray exec(String sql);
  external void close();
}










// @JS()
// library sqljs;

// import 'dart:typed_data';
// import 'dart:js_interop';

// @JS('initSqlJs')
// external JSPromise<SqlJsModule> initSqlJs([JSAny? config]);

// @JS()
// @staticInterop
// class SqlJsModule implements JSAny {}

// extension SqlJsModuleExtension on SqlJsModule {
//   external SqlJsDatabase Database([JSUint8Array? buffer]);
// }

// @JS()
// @staticInterop
// class SqlJsDatabase implements JSAny {}

// extension SqlJsDatabaseExtension on SqlJsDatabase {
//   external JSArray exec(String sql);
//   external void close();
// }







// @JS()
// library sqljs;

// import 'dart:typed_data';
// import 'dart:js_interop';

// @JS('initSqlJs')
// external JSAny? initSqlJs([JSAny? config]);

// @JS()
// @staticInterop
// class SqlJs {}

// extension SqlJsExtension on SqlJs {
//   external SqlJsDatabase Database(JSUint8Array buffer);
// }

// @JS()
// @staticInterop
// class SqlJsDatabase {}

// extension SqlJsDatabaseExtension on SqlJsDatabase {
//   external JSArray exec(String sql);
//   external void close();
// }







// @JS()
// library sqljs;

// import 'dart:typed_data';
// import 'dart:js_interop';

// @JS('initSqlJs')
// external dynamic initSqlJs([dynamic config]);

// @JS()
// @anonymous
// class SqlJs {
//   external SqlJsDatabase Database(Uint8List buffer);
// }

// @JS()
// @anonymous
// class SqlJsDatabase {
//   external List<dynamic> exec(String sql);
//   external void close();
// }






// @JS()
// library sqljs;

// import 'dart:typed_data';
// import 'package:js/js.dart';
// import 'dart:js_util';

// @JS('initSqlJs')
// external dynamic initSqlJs([dynamic config]);

// @JS()
// @anonymous
// class SqlJs {
//   external SqlJsDatabase Database(Uint8List buffer);
// }

// @JS()
// @anonymous
// class SqlJsDatabase {
//   external List<dynamic> exec(String sql);
//   external void close();
// }