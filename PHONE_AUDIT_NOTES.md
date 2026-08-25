# ملاحظات تدقيق مسار الهاتف

## مصادر خارجية

1. مستودع البناء المرجعي لـ Committee of Zero: https://github.com/CommitteeOfZero/sghd-patch
2. مستودع LanguageBarrier الأصلي: https://github.com/CommitteeOfZero/LanguageBarrier
3. المصدر الخام المستخدم للمقارنة: https://raw.githubusercontent.com/CommitteeOfZero/LanguageBarrier/main/LanguageBarrier/GameText.cpp

## نتائج مؤكدة

- `LanguageBarrier` في مستودع `sghd-patch` هو submodule يشير إلى مستودع `CommitteeOfZero/LanguageBarrier`، وليس مجلدًا عاديًا داخل المستودع.
- `drawPhoneTextHook` مسار عام مستقل، وتوقيعه يستقبل `textureId, xOffset, yOffset, lineLength, sc3string, lineSkipCount, lineDisplayCount, color, baseGlyphSize, opacity`.
- التنفيذ الأصلي يمرر `xOffset` و`lineLength` إلى `processSc3TokenList` ثم يرسم glyphs كما خرجت من التخطيط، دون محاذاة RTL إضافية.
- توجد مسارات منفصلة للبريد التفاعلي: `sghdDrawInteractiveMailHook`، ولحساب الروابط: `sghdGetLinksFromSc3StringHook`، ولتظليل الرابط: `sghdDrawLinkHighlightHook`.
- توجد دوال أخرى منفصلة لنص البريد في SGLBP/SGP: `sgpDrawMailTextHook` و`sgpDrawMailTextContentHook`، كما توجد دالة منفصلة لاسم مكالمة الهاتف `drawPhoneCallNameHook`.
- الإصلاح الحالي يطبق `rtlAlignPhoneLines` داخل `drawPhoneTextHook` فقط؛ لذلك لا يؤثر مباشرة في `sghdDrawInteractiveMailHook` أو `sgpDrawMailTextHook` أو `drawPhoneCallNameHook`، لكنه يؤثر في كل الاستدعاءات التي تمر عبر `drawPhoneTextHook`.
- المصدر الأصلي يحتوي إصلاحًا خاصًا لمستلم البريد في SGMDE عندما `lineLength == 252`، وإصلاحًا لـ `xOffset == 913`؛ وهذا يوضح أن `drawPhoneTextHook` يستقبل أنواعًا متعددة من نصوص الهاتف/البريد وليس نوعًا واحدًا فقط.
- تعريف SGLBP المحلي يذكر `coordsMultiplier=1.5`، `hasSghdPhone=true`، و`sghdPhoneXPadding=2`.

## الاستنتاج الأولي

لا يصح افتراض أن كل استدعاءات `drawPhoneTextHook` تمثل جسم رسالة هاتف يمكن محاذاته إلى اليمين. يلزم إما تسجيل معاملات الاستدعاءات في نسخة تشخيصية ثم بناء allowlist للحالات الآمنة، أو جعل RTL للهاتف معطلاً افتراضيًا مع خيار انتقائي. يجب عدم تعديل مسار الحوار المكتمل.

## تدقيق جديد: LTR للهاتف ومسار @Channel

- `drawPhoneCallNameHook` مسار مستقل عن `drawPhoneTextHook`، لذلك اسم المتصل لا يحتاج أن يرث محاذاة جسم الرسالة، ويجب إبقاؤه LTR.
- `sghdDrawInteractiveMailHook` هو مسار رسم البريد التفاعلي، والتعليق في المصدر يذكر أنه يُستخدم أيضًا لخيوط `@Channel`.
- مسارا `sghdGetLinksFromSc3StringHook` و`sghdDrawLinkHighlightHook` يحسبان مواضع الروابط بصورة مستقلة؛ أي إزاحة RTL للرسم وحده ستكسر hitboxes/highlights ما لم تُطبّق المعادلة نفسها عليهما.
- مسارا `sgpDrawMailTextHook` و`sgpDrawMailTextContentHook` منفصلان عن SGHD التفاعلي، ويستخدمان `startX/startY/lineLength` مع line count ثابتين، لذا لا يصح دمجهما تلقائيًا في أول إصلاح.
- عبارات الحالة مثل `Sending mail`, `Mail sent`, و`Calling` تحتاج allowlist أو تمييزًا من معاملات الاستدعاء/النص الخام؛ لا يجوز افتراض أنها جسم رسالة متعدد الأسطر.


## إصلاح v12: عزل عناصر حالة الاتصال

- أضيف `rtlPhoneVisibleLineCount` ليحسب الأسطر المرئية فعليًا من glyphs التي ستُرسم، بدل الاعتماد على `lineSkipCount` و`lineDisplayCount` اللذين قد يحملان قيمًا تبدو كأنها تمرير حتى في عناصر الحالة القصيرة.
- أصبحت `rtlPhoneCallAllowsAlignment` ترفض محاذاة أي نتيجة مرئية من سطر واحد عندما يكون `rtlPhoneMultilineOnly=true`. وبذلك تبقى `Calling` و`Mail sent` وأسماء/عناوين الصفوف في إحداثياتها الأصلية.
- `drawPhoneCallNameHook` لا يستدعي أي helper RTL، وأضيف تعليق صريح يثبت أن اسم المتصل/حالة الاسم خارج محاذاة جسم الرسائل.
- `drawChatMessageHook` لا يستدعي أي helper RTL، وأضيف تعليق صريح يثبت أن فقاعة المكالمة تبقى على مسارها LTR الأصلي.
- لا يوجد تغيير في ترتيب glyphs أو Arabic shaping أو منطق الحوار؛ التغيير الوحيد هو قرار تطبيق الإزاحة على جسم الهاتف متعدد الأسطر.
