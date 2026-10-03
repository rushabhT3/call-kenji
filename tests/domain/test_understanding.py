from datetime import date

import pytest

from kenji.domain.identity import DebtorIdentity
from kenji.domain.understanding import (
    find_birth_date,
    find_month_day,
    find_monthly_yen,
    is_plain_agreement,
    mentions_relative_timing,
    names_the_debtor,
    only_identity_words,
    only_offer_words,
)

BIRTHDAY = date(1990, 7, 14)
TODAY = date(2026, 10, 2)
DEBTOR = DebtorIdentity(
    family_name_kana="さとう",
    given_name_kana="ゆうき",
    written_name="佐藤ゆうき",
    family_name_written="佐藤",
    family_name_latin="Sato",
    date_of_birth=BIRTHDAY,
)
KENTA = DebtorIdentity(
    family_name_kana="たなか",
    given_name_kana="けんた",
    written_name="田中けんた",
    family_name_written="田中",
    family_name_latin="Tanaka",
    date_of_birth=date(1985, 3, 2),
)
HARUKA = DebtorIdentity(
    family_name_kana="すずき",
    given_name_kana="はるか",
    written_name="鈴木はるか",
    family_name_written="鈴木",
    family_name_latin="Suzuki",
    date_of_birth=date(1996, 11, 23),
)
MASARU = DebtorIdentity(
    family_name_kana="いとう",
    given_name_kana="まさる",
    written_name="伊藤まさる",
    family_name_written="伊藤",
    family_name_latin="Ito",
    date_of_birth=date(1972, 5, 9),
)
AYA = DebtorIdentity(
    family_name_kana="やまもと",
    given_name_kana="あや",
    written_name="山本あや",
    family_name_written="山本",
    family_name_latin="Yamamoto",
    date_of_birth=date(2000, 1, 30),
)


@pytest.mark.parametrize(
    "speech",
    [
        "佐藤ゆうきです。生年月日は平成2年7月14日です。",
        "生年月日は、平成2年7月14日です。",
        "1990年7月14日生まれです",
        "１９９０年７月１４日です",
        "平成 2年 7月 14日",
        "1990/7/14",
        "1990-07-14です",
        "平成二年七月十四日生まれです",
        "一九九〇年七月十四日です",
        "平成2年7月14日、平成2年7月14日です",
    ],
)
def test_one_date_of_birth_is_found(speech: str) -> None:
    assert find_birth_date(speech) == BIRTHDAY


def test_the_first_year_of_an_era_is_read() -> None:
    assert find_birth_date("平成元年1月8日です") == date(1989, 1, 8)


@pytest.mark.parametrize(
    ("speech", "expected"),
    [
        ("昭和60年3月2日です", date(1985, 3, 2)),
        ("昭和六十年三月二日生まれです", date(1985, 3, 2)),
        ("昭和 47年 5月 9日", date(1972, 5, 9)),
        ("昭和四十七年五月九日です", date(1972, 5, 9)),
        ("１９７２年５月９日です", date(1972, 5, 9)),
        ("昭和元年12月25日です", date(1926, 12, 25)),
        ("昭和64年1月7日です", date(1989, 1, 7)),
        ("平成八年十一月二十三日です", date(1996, 11, 23)),
        ("平成12年1月30日生まれです", date(2000, 1, 30)),
    ],
)
def test_a_date_of_birth_in_any_personas_era_is_read(speech: str, expected: date) -> None:
    assert find_birth_date(speech) == expected


@pytest.mark.parametrize(
    "speech",
    [
        "佐藤ゆうきです。",
        "平成2年7月14日、いや7月15日です",
        "平成2年7月14日か1990年7月15日",
        "2月30日",
        "平成2年2月30日です",
        "7月14日です",
        "平成二十二十年七月十四日",
        "平成〇十年七月十四日",
        "平成二二年七月十四日",
    ],
)
def test_no_date_or_an_unclear_one_is_left_to_the_model(speech: str) -> None:
    assert find_birth_date(speech) is None


@pytest.mark.parametrize(
    ("speech", "expected"),
    [
        ("10月20日でお願いします", date(2026, 10, 20)),
        ("初回は１０月２０日です", date(2026, 10, 20)),
        ("十月二十日で", date(2026, 10, 20)),
        ("1月5日にします", date(2027, 1, 5)),
        ("10月2日", TODAY),
        ("2026年11月1日", date(2026, 11, 1)),
    ],
)
def test_a_payment_date_is_the_next_one_to_come(speech: str, expected: date) -> None:
    assert find_month_day(speech, TODAY) == expected


@pytest.mark.parametrize(
    "speech",
    [
        "来月の20日で",
        "20日で",
        "10月20日か10月25日",
        "2026年11月1日、いや11月2日",
        "2026年11月1日か2026年11月2日",
        "2月30日",
        "2026年2月30日",
        "平成二二年七月十四日",
        "来週でお願いします",
    ],
)
def test_an_unclear_payment_date_is_left_to_the_model(speech: str) -> None:
    assert find_month_day(speech, TODAY) is None


def test_february_29_is_none_when_no_leap_year_comes_next() -> None:
    assert find_month_day("2月29日", date(2026, 3, 1)) is None


@pytest.mark.parametrize(
    ("speech", "expected"),
    [
        ("月3000円なら払えます", 3_000),
        ("毎月6,000円でお願いします", 6_000),
        ("３０００円です", 3_000),
        ("6千円で", 6_000),
        ("三千円しか払えません", 3_000),
        ("1万円なら", 10_000),
        ("1万5千円", 15_000),
        ("一万五千円", 15_000),
        ("1万5000円", 15_000),
        ("6千500円", 6_500),
        ("15,000円で", 15_000),
        ("6000円、はい、6000円で", 6_000),
    ],
)
def test_one_monthly_amount_is_read(speech: str, expected: int) -> None:
    assert find_monthly_yen(speech) == expected


@pytest.mark.parametrize(
    "speech",
    [
        "払えません",
        "全部で35,000円です",
        "一括で35,000円払います",
        "合計で1万円",
        "3000円か4000円",
        "35,000円は無理なので月6000円",
        "0円です",
        "何千円か払えます",
        "数万円",
        "千円",
        "15千円",
        "6千1500円",
        "1万15000円",
        "円",
        "平成二二千円",
    ],
)
def test_an_unclear_amount_is_left_to_the_model(speech: str) -> None:
    assert find_monthly_yen(speech) is None


@pytest.mark.parametrize(
    "speech",
    [
        "佐藤ゆうきです。",
        "佐藤 ゆうき です",
        "さとうゆうきです",
        "サトウユウキです",
        "佐藤ユウキです",
        "はい、佐藤ゆうきです。生年月日は平成2年7月14日です。",
    ],
)
def test_the_account_holders_full_name_is_recognised(speech: str) -> None:
    assert names_the_debtor(speech, DEBTOR)


@pytest.mark.parametrize(
    "speech",
    [
        "佐藤です",
        "佐藤の妻です。主人はいま出かけています。",
        "佐藤ゆうきの妻です",
        "佐藤ゆうきさんの件で電話しました",
        "佐藤ゆうきの母です",
        "田中ひろしです",
        "佐藤ゆうきの代理の者です",
        "本人ではないですが、佐藤ゆうきの家族です",
    ],
)
def test_someone_else_or_a_partial_name_is_not_the_account_holder(speech: str) -> None:
    assert not names_the_debtor(speech, DEBTOR)


@pytest.mark.parametrize(
    ("speech", "debtor"),
    [
        ("田中けんたです。生年月日は、昭和60年3月2日です。", KENTA),
        ("タナカケンタです。昭和六十年三月二日生まれです。", KENTA),
        ("鈴木はるかです。生年月日は、平成8年11月23日です。", HARUKA),
        ("伊藤まさると申します。昭和47年5月9日生まれです。", MASARU),
        ("はい、本人です。いとうまさる、生年月日は1972年5月9日です。", MASARU),
        ("山本あやです。生年月日は2000年1月30日です。", AYA),
    ],
)
def test_every_personas_name_and_birth_date_are_left_for_the_rules(
    speech: str, debtor: DebtorIdentity
) -> None:
    assert find_birth_date(speech) == debtor.date_of_birth
    assert names_the_debtor(speech, debtor)
    assert only_identity_words(speech, debtor)


@pytest.mark.parametrize(
    ("speech", "debtor"),
    [
        ("田中です", KENTA),
        ("けんたです", KENTA),
        ("田中の家族です。本人はいま出かけています。", KENTA),
        ("田中けんたの父です", KENTA),
        ("伊藤まさるさんの件で電話しました", MASARU),
        ("佐藤ゆうきです", MASARU),
        ("山本の家族です。本人はいま出かけています。", AYA),
    ],
)
def test_someone_else_or_a_partial_name_is_not_another_persona(
    speech: str, debtor: DebtorIdentity
) -> None:
    assert not names_the_debtor(speech, debtor)


def test_another_personas_identity_is_not_this_debtors() -> None:
    speech = "佐藤ゆうきです。生年月日は、平成2年7月14日です。"

    assert not names_the_debtor(speech, KENTA)
    assert find_birth_date(speech) != KENTA.date_of_birth


@pytest.mark.parametrize(
    "speech",
    [
        "はい",
        "はい。",
        "はーい",
        "ええ",
        "はい、お願いします。",
        "それでお願いします",
        "大丈夫です",
        "間違いありません",
        "はい、それで結構です。",
        "はい、間違いありません。",
        "お願いします",
        "その内容でお願いします",
        "ハイ、ダイジョウブデス",
    ],
)
def test_a_plain_yes_is_agreement(speech: str) -> None:
    assert is_plain_agreement(speech)


@pytest.mark.parametrize(
    "speech",
    [
        "",
        "。",
        "いいえ、違います",
        "はい、でも来月なら",
        "6000円なら払えます",
        "はい、6000円で",
        "大丈夫ですか？",
        "それでいいですか?",
        "結構です",
        "いいです",
        "はい、ちょっと待ってください",
        "はい、日付を変えてください",
        "担当者と話したいです",
        "はい、お願いします。はい、お願いします。はい、お願いします。",
        "はい、考えさせてください",
    ],
)
def test_anything_beyond_a_plain_yes_is_left_to_the_model(speech: str) -> None:
    assert not is_plain_agreement(speech)


@pytest.mark.parametrize(
    ("speech", "is_relative"),
    [
        ("毎月6,000円、初回は来週でお願いします。", True),
        ("来月から6,000円なら払えます。", True),
        ("給料日のあとにお願いします。", True),
        ("毎月6,000円、初回は10月20日でお願いします。", False),
        ("今月は仕事が減って苦しいです。毎月6,000円なら払えます。", False),
    ],
)
def test_relative_timing_is_noticed(speech: str, is_relative: bool) -> None:
    assert mentions_relative_timing(speech) is is_relative


@pytest.mark.parametrize(
    "speech",
    [
        "佐藤ゆうきです。生年月日は、平成2年7月14日です。",
        "佐藤ゆうきです。平成2年7月14日生まれです。",
        "サトウユウキと申します。1990年7月14日生まれです。",
        "はい、本人です。佐藤ゆうき、生年月日は1990年7月14日です。",
    ],
)
def test_a_name_and_birth_date_alone_are_left_for_the_rules(speech: str) -> None:
    assert only_identity_words(speech, DEBTOR)


@pytest.mark.parametrize(
    "speech",
    [
        "佐藤ゆうきです。平成2年7月14日生まれです。もう電話してこないでください。",
        "佐藤ゆうきです。平成2年7月14日です。担当者の方と話したいです。",
        "佐藤ゆうきです。平成2年7月14日です。弁護士に相談しています。",
        "佐藤ゆうきです。平成2年7月14日です。いくら払えばいいですか。",
        "佐藤ゆうきです。平成二二年七月十四日です。",
    ],
)
def test_a_name_and_birth_date_with_anything_more_go_to_the_model(speech: str) -> None:
    assert not only_identity_words(speech, DEBTOR)


@pytest.mark.parametrize(
    "speech",
    [
        "今月はちょっと厳しくて、月3000円なら払えます。",
        "毎月6,000円でお願いします。",
        "3,000円しか払えません。",
        "わかりました、6,000円にします。",
        "毎月6,000円で、初回は10月20日でお願いします。",
    ],
)
def test_an_amount_alone_is_left_for_the_rules(speech: str) -> None:
    assert only_offer_words(speech)


@pytest.mark.parametrize(
    "speech",
    [
        "毎月6,000円なら払えますが、人間の担当者と話したいです。",
        "6,000円なら払えます。でも、もう連絡しないでください。",
        "毎月6,000円なら払えます。弁護士に相談しています。",
        "今月は仕事が減って苦しいです。毎月6,000円なら払えます。",
        "6,000円なら払えますけど、手数料はかかりますか。",
        "三二千円なら払えます。",
    ],
)
def test_an_amount_with_anything_more_goes_to_the_model(speech: str) -> None:
    assert not only_offer_words(speech)
