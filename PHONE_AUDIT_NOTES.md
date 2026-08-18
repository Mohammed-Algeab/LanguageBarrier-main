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
