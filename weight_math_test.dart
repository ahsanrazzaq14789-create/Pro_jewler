import 'package:flutter_test/flutter_test.dart';
import 'package:gold_silver_mobile/weight_math.dart';
void main(){
 test('one tola grams',()=>expect(WeightMath.tolaToGrams(1),closeTo(11.6638,0.00001)));
 test('22k pure gold',()=>expect(WeightMath.pureGoldGrams(10,22),closeTo(9.1666667,0.0001)));
 test('sale value',()=>expect(WeightMath.saleValue(grams:11.6638,ratePerTola:250000),closeTo(250000,0.01)));
}
