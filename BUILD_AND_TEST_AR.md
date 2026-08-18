# دليل بناء واختبار LanguageBarrier RTL على Windows

## المتطلبات

يحتاج المشروع إلى Windows 10 أو أحدث، وVisual Studio 2022 مع workload باسم **Desktop development with C++**، وWindows SDK، وملفات MSVC x86. يجب أن يكون الهدف `Win32` لأن ملف المشروع لا يبني DLL بمعمارية x64.

يحتاج المشروع أيضاً إلى vcpkg حتى تُبنى الاعتماديات المحددة في `vcpkg.json`: MinHook وDirectXTex وFreeType وnlohmann-json وCereal وImGui وbetter-enums. لا تستخدم نسخة DLL من منصة مختلفة عن اللعبة؛ لعبة Steins;Gate القديمة تحتاج عادةً DLL ‏32-bit.

## البناء عبر Developer Command Prompt

افتح **x86 Native Tools Command Prompt for VS 2022**، وانتقل إلى مجلد المشروع المعدل:

```bat
cd /d C:\path\to\LanguageBarrier-main
```

إذا لم يكن vcpkg مثبتاً، ثبّته بالطريقة المعتادة ثم فعّل تكامل MSBuild:

```bat
git clone https://github.com/microsoft/vcpkg C:\vcpkg
C:\vcpkg\bootstrap-vcpkg.bat
C:\vcpkg\vcpkg integrate install
```

بعد ذلك افتح الحل أو ابنِه مباشرةً:

```bat
msbuild LanguageBarrier.sln /m /p:Configuration=dinput8-Release /p:Platform=Win32
```

لنسخة Debug:

```bat
msbuild LanguageBarrier.sln /m /p:Configuration=dinput8-Debug /p:Platform=x86
```

الناتج المتوقع هو `dinput8.dll` داخل مجلد `bin` أو مجلد الإخراج الذي يحدده Visual Studio. إعدادات `cryptbase-Release` و`cryptbase-Debug` تنتج `cryptbase.dll` بدلاً من `dinput8.dll`، ولا ينبغي اختيارها إلا إذا كان patch المستهدف يستخدم طريقة تحميل cryptbase.

إذا فشل MSBuild في إيجاد الاعتماديات، نفّذ بناء vcpkg للـ triplet x86 ثم أعد المحاولة. لا تنشئ `LanguageBarrier/contrib/lib/Release` يدويًا؛ النسخة الحالية تستخدم `contrib/lib/xy-vsfilter`، وقد أزيل مسار Release القديم من إعدادات Release في ملف المشروع لأن المستودع لا يحتوي مكتبات فعلية فيه:

```bat
C:\vcpkg\vcpkg install --triplet x86-windows-static-md
msbuild LanguageBarrier.sln /m /p:Configuration=dinput8-Release /p:Platform=x86 /p:VcpkgUserTriplet=x86-windows-static-md /p:VcpkgEnabled=true
```

في هذا الحل تحديدًا، اسم المنصة في `LanguageBarrier.sln` هو `x86`، بينما mapping داخل ملف الحل يوجهها إلى مشروع `LanguageBarrier.vcxproj` بمنصة `Win32`. لذلك يجب استعمال `/p:Platform=x86` عند بناء ملف `.sln`. أما vcpkg فيستخدم `x86-windows-static-md` لتحديد معمارية الحزم؛ وهما اسمان مختلفان بطبيعة الحال. يجب أن توجد الملفات `LanguageBarrier/contrib/lib/xy-vsfilter/VSFilter.lib` و`VSFilter.dll`، إضافة إلى `LanguageBarrier/contrib/include`؛ ولا توجد حاجة لمجلد `contrib/lib/Release`.

## تفعيل الوضع

في ملف patch configuration الخاص بنسخة اللعبة، أضف الإعدادات التالية:

```json
{
  "patch": {
    "rtlDialogue": true,
    "rtlDialogueRightX": 1200,
    "rtlDialogueKeepNameLine": true,
    "rtlPhone": true,
    "rtlPhoneMultilineOnly": true,
    "rtlPhoneRightX": 120
  }
}
```

يجب إبقاء `rtlDialogue` مفعلاً فقط أثناء الاختبار، وضبط `rtlDialogueReverseText` على `false`. الكود يقرأ الخيارات عند `gameTextInit()`، ثم يركّب hooks `drawDialogue` و`drawDialogue2` لمسار الحوار العام حتى لو كان `improveDialogueOutlines` غير مفعّل. في النسخة fixed لا يُستخدم `rtlDialogueReverseText` إطلاقًا لعكس مصدر glyph؛ كل glyph وقياس وصندوق وجهة ولون يأتي من الفهرس نفسه `i`. إذا كانت `rtlDialogueRightX` موجبة، تُنقل الأسطر كلها أفقيًا إلى الحافة اليمنى من دون عكس ترتيب مواضع glyphs، ثم يُعكس مصدر `charDisplayOpacity` فقط لكل سطر كي يظهر الـtypewriter من آخر خانة مرئية إلى أولها. هذا يمنع تفاوت الأحجام الناتج عن خلط source glyph بصندوق وجهة مختلف، ولا يغيّر السكربت أو Backlog أو الهاتف أو النصوص العامة.

## ترتيب الاختبار

انسخ DLL الناتج إلى مجلد اللعبة وفق طريقة patch الأصلية، واحتفظ بنسخة احتياطية من DLL والملفات الأصلية. لا تختبر فوق ملف الحفظ الوحيد؛ استخدم مشهداً قصيراً يمكن تكراره.

ابدأ بجملة عربية قصيرة من كلمتين أو ثلاث. لم يعد `rtlDialogueReverseText` موجودًا في patchdef المنظف؛ لا تضف reverse آخر. يجب أن يظهر كل glyph من مصدره الأصلي وبحجمه المتسق، وأن ينتقل السطر ككتلة إلى اليمين إذا كانت `rtlDialogueRightX` موجبة، مع بقاء ترتيب glyphs النسبي كما بُني في الصفحة. راقب الكتابة التدريجية: يجب أن تظهر الخانة اليمنى أولًا ثم التي تليها بصريًا نحو اليسار. لا تغيّر ترتيب النص في الملفات ولا تفعل reverse خارج DLL أثناء هذا الاختبار.

لاختبار الهاتف، ابدأ بالإعداد الآمن `rtlPhone: true` مع `rtlPhoneMultilineOnly: true` و`rtlPhoneRightX: 120`. لا تُستخدم قيمة 120 كإحداثي شاشة مطلق؛ بل كـ**إزاحة داخلية اختيارية** مقدارها 120 بكسل نهائيًا من الحافة اليمنى التي يحسبها الكود من `xOffset + lineLength` بعد تطبيق padding الهاتف الأصلي. في الوضع الآمن، لا تُحاذى تلقائيًا الاستدعاءات أحادية السطر غير القابلة للتمرير؛ لأن مسار `drawPhoneTextHook` مشترك بين جسم الرسالة وبين أسماء أو عناوين أو تسميات وعناصر قائمة. أما الاستدعاءات متعددة الأسطر أو التي تحمل `lineSkipCount` للتمرير فتُحاذى كسطور كاملة عبر تحريك `displayStartX` و`displayEndX` معًا. بذلك لا تتأثر العناصر أحادية السطر التي سببت الخلل السابق. يمكن ضبط `rtlPhoneRightX` إلى `0` إذا كان inset 120 كبيرًا في إطار هاتف النسخة المستخدمة. البريد التفاعلي ومسارات `sgpDrawMailText` لا تتأثر بهذا المفتاح.

بعد ذلك اختبر في الهاتف جسم رسالة طويلًا يلتف إلى سطرين، ثم انتقل إلى شاشة تحتوي اسمًا أو عنوانًا أو صفًا قصيرًا. يجب أن يتحرك جسم الرسالة فقط في الوضع الآمن، بينما يبقى الاسم والعنوان في موضعهما الأصلي. لا توجد كتابة تدريجية خاصة بالهاتف هنا؛ لذلك لا نحتاج إلى عكس opacity كما في الحوار. اختبر أيضًا رسالة قصيرة من سطر واحد؛ بقاءها LTR في الوضع الآمن مقصود، وهو أفضل من إزاحة عنصر واجهة إلى موضع خاطئ. إذا أردت تجربة المحاذاة العامة لكل الاستدعاءات، اضبط `rtlPhoneMultilineOnly: false` مؤقتًا، لكن لا تعتمد ذلك قبل اختبار كل شاشات الهاتف.

## قراءة النتيجة

| النتيجة | التفسير المحتمل |
|---|---|
| لا يوجد تغيير إطلاقاً | DLL غير محمّل، أو patch يستخدم configuration آخر، أو signatures لا تطابق executable |
| السطر ينتقل إلى اليمين لكن ترتيب glyphs أو القراءة غير صحيح | الإزاحة الجماعية تعمل، لكن ترتيب بيانات السكربت أو mapping الخط يحتاج مراجعة؛ لا تضف reverse ثانيًا |
| الإطار النهائي صحيح لكن الظهور التدريجي يبدأ من الطرف الخطأ | راجع `dialogueGlyphIndexForReveal()` ومطابقة `charDisplayY` لكل سطر؛ لا تغيّر `renderIndex` ولا مواضع glyphs |
| الأحجام متساوية لكن اتصال العربية غير صحيح | اتجاه الرسم يعمل، لكن shaping/contextual forms غير موجودة في أطلس اللعبة؛ هذه مرحلة مستقلة عن RTL |
| السطر الثاني يبدأ من الطرف الخطأ | helper يجمع glyphs حسب `fontNumber` و`charDisplayY`؛ افحص log قبل تغيير أي مسار عام |
| crash عند بدء اللعبة | DLL أو configuration غير متوافق، أو signature خاطئة؛ أعد DLL الأصلي وافحص `languagebarrier\log.txt` |

## فحص السجل

بعد التشغيل، راجع:

```text
languagebarrier\log.txt
```

تأكد من ظهور اسم اللعبة واسم patch وعدم وجود فشل في `drawDialogue` أو signature scanning. يجب أن يظهر أيضًا سطر يبدأ بـ `RTL dialogue config:`، وأن تتضمن قيمه `phoneEnabled=1` و`phoneMultilineOnly=1` و`phoneRightInset=120` عند اختبار الوضع الآمن. إذا ظهرت مشكلة في أي عنصر هاتف، عطّل الهاتف بالكامل بوضع `rtlPhone: false`؛ سيبقى الحوار RTL كما هو، ويعود الهاتف إلى تخطيطه الأصلي LTR دون الحاجة إلى حذف hooks الهاتف الأخرى. إذا لم يصل التنفيذ إلى hook، أرسل ملف السجل وملف `gamedef.json` المستخدم، لأن الأرشيف الحالي يحتوي core العام ولا يحتوي signatures خاصة بإصدار آخر غير SGLBP patch المرجعي.

## حدود النسخة الحالية

هذه النسخة لا تنفذ shaping عربيًا؛ فهي تتعامل مع النص كما تتعامل اللعبة مع glyph IDs، لأن النص العربي في السكربت معكوس مسبقًا والخط هو الذي يقدّم الشكل العربي. إذا ظهرت حروف منفصلة أو أشكال غير صحيحة، فذلك يعني أن مرحلة mapping إلى أطلس الخط تحتاج معالجة مستقلة لاحقًا، وليس أن المطلوب reverse آخر. الحوار يبقى المسار RTL الكامل مع typewriter من اليمين إلى اليسار. الهاتف أصبح مسارًا انتقائيًا محافظًا: `rtlPhoneMultilineOnly: true` يحمي النصوص أحادية السطر المشتركة، و`rtlPhoneRightX` يعمل كـinset فقط عند محاذاة الاستدعاء. إذا لم تكن المحاذاة الانتقائية مرضية في نسخة اللعبة، فالخيار الصحيح هو `rtlPhone: false` وقبول الهاتف LTR، بدل إفساد أسماء وعناوين وعناصر واجهة الهاتف. يبقى Backlog خارج هذا التعديل عمدًا، ولا يتغير البريد التفاعلي بهذا المفتاح.
 بناء DLL فعلي لم يتم داخل بيئة Ubuntu الحالية لغياب MSVC وWindows SDK؛ يجب تنفيذ الأوامر أعلاه على Windows أو عبر GitHub Actions أو بيئة Visual Studio متوافقة.
