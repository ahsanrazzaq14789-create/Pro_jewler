import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class LocalStore {
 static Database? _db;
 static Future<Database> get db async {
  if(_db!=null)return _db!;
  final path=join(await getDatabasesPath(),'gold_silver_offline.db');
  _db=await openDatabase(path,version:1,onCreate:(d,v)async{
   await d.execute('CREATE TABLE records(id TEXT PRIMARY KEY, shop_id INTEGER,module TEXT,payload TEXT,updated_at TEXT,synced INTEGER DEFAULT 0)');
   await d.execute('CREATE TABLE sync_queue(id INTEGER PRIMARY KEY AUTOINCREMENT,record_id TEXT,operation TEXT,payload TEXT,created_at TEXT)');
  });return _db!;
 }
 static Future<void> cache(Map<String,dynamic> record,int shopId) async {
  final d=await db;await d.insert('records',{'id':record['id'],'shop_id':shopId,'module':record['module'],'payload':jsonEncode(record),'updated_at':record['updated_at']??DateTime.now().toIso8601String(),'synced':1},conflictAlgorithm:ConflictAlgorithm.replace);
 }
 static Future<List<Map<String,dynamic>>> records(int shopId,String module) async {
  final d=await db;final rows=await d.query('records',where:'shop_id=? AND module=?',whereArgs:[shopId,module],orderBy:'updated_at DESC');
  return rows.map((x)=>jsonDecode(x['payload'] as String) as Map<String,dynamic>).toList();
 }
 static Future<void> queue(String id,String operation,Map<String,dynamic> payload) async {
  final d=await db;await d.insert('sync_queue',{'record_id':id,'operation':operation,'payload':jsonEncode(payload),'created_at':DateTime.now().toIso8601String()});
 }
 static Future<List<Map<String,Object?>>> pending() async => (await db).query('sync_queue',orderBy:'id');
 static Future<void> removeQueue(int id) async => (await db).delete('sync_queue',where:'id=?',whereArgs:[id]);
}
