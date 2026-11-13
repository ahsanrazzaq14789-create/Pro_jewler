class WeightMath {
  static const gramsPerTola=11.6638;
  static double gramsToTola(double grams)=>grams/gramsPerTola;
  static double tolaToGrams(double tola)=>tola*gramsPerTola;
  static double pureGoldGrams(double gross,double karat)=>gross*(karat/24);
  static double saleValue({required double grams,required double ratePerTola, double making=0,double discount=0}) =>
    (gramsToTola(grams)*ratePerTola+making-discount).clamp(0,double.infinity);
  static double silverValue({required double grams,required double ratePerTola,double making=0,double discount=0}) =>
    saleValue(grams:grams,ratePerTola:ratePerTola,making:making,discount:discount);
}
