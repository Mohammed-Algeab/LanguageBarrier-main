# دعم الحركات العربية في LanguageBarrier

## الحالة الافتراضية

ميزة الحركات اختيارية ومغلقة افتراضيًا بواسطة:

```json
"arabicHarakatEnabled": false
```

عند بقائها `false` لا يمر النص في مسار الحركات الجديد، ولا يتغير منطق RTL أو الحوار أو الهاتف الموجود. لتفعيلها، ضع `harakat.json` داخل مجلد `languagebarrier` بجانب DLL، ثم فعّل المفتاح في `patchdef.json`.

## ما هو معرف الحركة؟

المعرف الأساسي هو **glyph ID/index** وليس Unicode. هذا هو المعرف الذي تحمله خانات SC3 والذي تستخدمه اللعبة للوصول إلى خانة الصورة وإلى `width.bin`.

في النص الثنائي يحسب LanguageBarrier المعرف بهذه الصيغة:

```cpp
glyphId = lowByte + ((firstByte & 0x7F) << 8);
```

وفي مسار bitmap تكون الخانة عادةً مرتبطة بترتيب atlas، مثل:

```cpp
glyphId = column + row * FONT_ROW_LENGTH;
```

لذلك يجب وضع معرف الخانة الذي خصصته للحركة في `glyphIds` داخل `harakat.json`. لا تضع رقم Unicode مثل `1614` في `glyphIds` إلا إذا كان هذا هو فعلًا رقم خانة glyph في خط اللعبة؛ رقم Unicode `1614` يصلح فقط داخل قائمة `unicode` الاختيارية لمسار replacement font عندما تكون `fullCharMap` قد ربطت ذلك الـglyph بالحرف `U+064E`.

> الخلاصة: **لـSGHD/bitmap استخدم index الموجود في SC3 وwidth.bin. Unicode ليس المرجع الموثوق هناك.**

## صيغة `harakat.json`

الملف مستقل عن `patchdef.json` ويوضع في:

```text
languagebarrier/harakat.json
```

القالب المرفق يحتوي قوائم فارغة عمدًا. املأها بالـIDs الفعلية التي استعملتها للحركات:

```json
{
  "version": 1,
  "marks": {
    "fatha":     { "glyphIds": [1234], "glyphRanges": [], "unicode": [1614] },
    "damma":     { "glyphIds": [1235], "glyphRanges": [], "unicode": [1615] },
    "kasra":     { "glyphIds": [1236], "glyphRanges": [], "unicode": [1616] },
    "sukun":     { "glyphIds": [1237], "glyphRanges": [], "unicode": [1618] },
    "fathatan":  { "glyphIds": [1238], "glyphRanges": [], "unicode": [1611] },
    "dammatan":  { "glyphIds": [1239], "glyphRanges": [], "unicode": [1612] },
    "kasratan":  { "glyphIds": [1240], "glyphRanges": [], "unicode": [1613] },
    "shadda":    { "glyphIds": [1241], "glyphRanges": [], "unicode": [1617] }
  }
}
```

يمكن استخدام نطاقات بدل سرد كل خانة:

```json
"glyphRanges": [[1234, 1236], { "from": 1240, "to": 1242 }]
```

الأسماء `fatha`, `damma`, `sukun`, `fathatan`, و`dammatan` تعامل كحركات علوية. الأسماء `kasra`, و`kasratan` تعامل كحركات سفلية. `shadda` لها حالة مستقلة. إذا كان نفس الـID موجودًا في أكثر من فئة، فالأولوية هي: `shadda` ثم `kasra` ثم الحركة العلوية.

## إزاحات `patchdef.json`

كل حالة تملك إزاحتي **X وY** مستقلتين. الإزاحات تقاس في نفس فضاء إحداثيات الرسم الذي يستخدمه المسار، لذلك غيّرها تدريجيًا بالموجب والسالب:

```json
{
  "patch": {
    "arabicHarakatEnabled": true,

    "arabicHarakatUpperX": 0,
    "arabicHarakatUpperY": 0,

    "arabicHarakatKasraX": 0,
    "arabicHarakatKasraY": 0,

    "arabicHarakatShaddaX": 0,
    "arabicHarakatShaddaY": 0,

    "arabicHarakatShaddaUpperX": 0,
    "arabicHarakatShaddaUpperY": 0,

    "arabicHarakatShaddaKasraX": 0,
    "arabicHarakatShaddaKasraY": 0
  }
}
```

الحركة العلوية المفردة تستخدم `arabicHarakatUpperX/Y`. الكسرة المفردة تستخدم `arabicHarakatKasraX/Y`. الشدة تستخدم `arabicHarakatShaddaX/Y`. أي حركة علوية مع شدة تستخدم `arabicHarakatShaddaUpperX/Y`. الكسرة مع شدة تستخدم `arabicHarakatShaddaKasraX/Y`، وتبقى نقطة ارتكازها تحت الحرف الأساسي وفق المستطيل المحسوب، لا تحت شدة منفصلة.

## ترتيب الإدخال والكتابة التدريجية

لا يعتمد اكتشاف cluster على ترتيب الحركة والشدة. فإذا جاء الإدخال `base + shadda + fatha` أو `base + fatha + shadda`، يبحث المسار في كامل مجموعة الحرف الأساسي أولًا، ثم يحدد هل توجد شدة ويطبق إزاحة الحالة المناسبة.

كل حركة ترتبط بآخر حرف أساسي في نفس السطر. الفراغ و[linebreak] يقطعان الارتباط، فلا تنتقل حركة بداية كلمة أو سطر إلى الحرف السابق. advance المرئي يبقى موجبًا حتى تُرسم الخانة، لكن advance المنطقي للحركة يصبح صفرًا في القياس والتفاف السطر وموضع الحروف التالية.

في مسار الحوار، opacity/reveal للحركة مربوط بالحرف الأساسي حتى لا تظهر الحركة قبل حرفها ولا تزيد عدد الحروف التي تكشفها الكتابة التدريجية. ووسم `[phone-ltr]` يتجاوز مسار RTL والحركات في الحوار كما كان مطلوبًا.

## `width.bin`

لا تجعل خانة الحركة `00`؛ الاختبار العملي في اللعبة أثبت أن القيمة الصفرية قد تمنع رسم glyph بالكامل. استخدم قيمة موجبة صغيرة مثل `05`، أو أصغر قيمة موجبة تثبت أنها تُرسم في نسختك. LanguageBarrier يتكفل بإلغاء أثرها المنطقي، لذلك لا تستخدم قيمة سالبة ولا تحاول تعديل `width.bin` من داخل DLL.

## حدود مسار الـbacklog

المسار الجديد موصول بمسار النص المعالج العام، ولذلك تستفيد منه مسارات الهاتف والبريد و`@Channel` عند مرورها عبر `processSc3TokenList`، كما يستمر دعم الحوار SGHD-style الخاص دون تغيير. أما الـbacklog فليس له renderer واحد في كل الألعاب؛ لذلك بقي المفتاح العام مستقلًا:

```json
"arabicHarakatStripBacklog": false
```

عند ضبطه على `true`، يتخطى renderer الـbacklog في مسارات RN/RND glyphs الحركات المعرفة في `harakat.json` أثناء القياس والرسم، فلا تظهر الحركة ولا تدفع الحرف التالي. لا يتم تعديل `BacklogText` الأصلي؛ التجاوز بصري ومحلي أثناء الرسم فقط.

### SGHD/STEINS;GATE الأصلية: مسار تجريبي محدود

في STEINS;GATE الأصلية/SGHD لا يُستخدم hook `DrawBacklogContentHookRNE/RND` نفسه. المسار المتاح في المصدر يمر عبر `drawSingleTextLineHook`، لكن هذا hook يخدم أكثر من نوع نص، ولذلك **لا يجوز استهداف كل `singleTextLineFixes` تلقائيًا**. أضيفت allowlist اختيارية:

```json
{
  "patch": {
    "arabicHarakatEnabled": true,
    "arabicHarakatStripBacklog": true,
    "arabicHarakatStripSghdCallsites": [
      "clearlistDrawRet1",
      "clearlistDrawRet2"
    ]
  }
}
```

يُفعّل هذا المسار فقط إذا كانت قيمتا `gamedef.drawGlyphVersion` و`gamedef.gameName` تساويان بالضبط `sghd` و`STEINS;GATE`، وإذا كان اسم الـcallsite موجودًا في القائمة وفي `singleTextLineFixes`. الأسماء المقبولة هي `clearlistDrawRet1` حتى `clearlistDrawRet13`. عدم وجود المفتاح أو ترك القائمة فارغة يعني **عدم حذف أي شيء**.

عند تفعيل callsite مصرح به، يُنسخ SC3 إلى buffer مؤقت، وتحذف فقط glyph tokens التي تصنفها `harakat.json`، مع إبقاء glyphs العادية، وcontrols الثابتة المعروفة، وتسلسل `0xFF 0xFF`. لا يُعدّل buffer اللعبة الأصلي، ولا يُعاد حساب `maxLength` لأن وحدته في هذا hook غير مثبتة هنا. إذا ظهر control متغير الطول مثل `0x04` أو control موجب غير معروف، يرجع المسار إلى النص الأصلي دون تعديل.

هذا **حل تجريبي ومحافظ**، وليس إثباتًا أن كل `clearlistDrawRet` هو backlog فعلًا. يجب تشغيل اللعبة مع تفعيل diagnostics، ثم فحص `languagebarrier\\log.txt` ومقارنة النص قبل/بعد. لا يمكن تأكيد أن SGHD backlog أصبح محلولًا نهائيًا من source وحده، ولا يُنصح بتفعيل كل الأسماء دفعة واحدة قبل معرفة callsite الذي يمرر backlog.

عند بقائه `false` لا يتغير سلوك الـbacklog القديم. لا يوجد في هذه النقطة أي تعديل لـCC أو SGMDE أو RTL أو الهاتف أو البريد أو Windows 7.
