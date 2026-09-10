# Plik Testowy z Tagami Markdown

Ten plik zawiera różne tagi Markdown do testowania tłumaczenia.

## Nagłówki

### Nagłówek H3
#### Nagłówek H4
##### Nagłówek H5
###### Nagłówek H6

## Formatowanie tekstu

**Tekst pogrubiony** i *tekst kursywy* i ***tekst pogrubiony i kursywy*** i ~~tekst przekreślony~~ i `inline code`.

## Listy

### Nieuporządkowana lista
- Element 1
- Element 2
  - Podelement 2.1
  - Podelement 2.2
- Element 3

### Uporządkowana lista
1. Pierwszy element
2. Drugi element
   1. Podelement 2.1
   2. Podelement 2.2
3. Trzeci element

### Lista zadań
- [x] Zakończone zadanie
- [ ] Zadanie w trakcie
- [ ] Inne zadanie w trakcie

## Linki i obrazy

[Tekst linku](https://example.com "Tytuł")

![Tekst alternatywny](https://example.com/image.png "Tytuł obrazu")

## Bloki cytowań

> To jest blok cytowania.
> Może się rozciągać na wiele wierszy.
>
> > Wewnętrzne blok cytowania.

## Bloki kodu

```python
def hello_world():
    print("Hello, World!")
    return 42
```

```javascript
function greet(name) {
    return `Hello, ${name}!`;
}
```

## Tabele

| Nagłówek 1 | Nagłówek 2 | Nagłówek 3 |
|----------|----------|----------|
| Komórka 1   | Komórka 2   | Komórka 3   |
| Komórka 4   | Komórka 5   | Komórka 6   |

| Lewo | Środek | Prawo |
|:-----|:------:|------:|
| L1   | C1     | R1    |
| L2   | C2     | R2    |

## Linie poziome

---
___

## HTML w Markdown

<div class="container">
  <p>To jest akapit w formacie HTML.</p>
  <ul>
    <li>Przedmiot listy HTML 1</li>
    <li>Przedmiot listy HTML 2</li>
  </ul>
</div>

## Znaky ucieczki

\*Nie jest kursywą\*

\# Nie jest nagłówkiem

\[Nie jest linkiem\]

## Przerwy w linii

Pierwsza linia
Druga linia (z dwoma spacjami na końcu)

Pierwsza linia
Druga linia (z ukośnikiem)

## Notki

Ten tekst ma notkę[^1] i kolejną[^note].

[^1]: To jest pierwsza notka.
[^note]: To jest notka o nazwie.

## Listy definicji

Termin 1
: Definicja 1

Termin 2
: Definicja 2a
: Definicja 2b

## Matematyka (jeśli obsługiwana)

Matematyka w linii: $E = mc^2$

Matematyka w bloku:
$$
\int_{0}^{\infty} e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
$$

## Emoji i znaki specjalne

✅ Znaczek "sprawdzone"
❌ Znaczek "odrzucone"
⚠️ Ostrzeżenie
 Memo

Specjalne: © ® ™ € £ ¥

## Mieszane treści

Ten akapit ma **tekst pogrubiony**, *tekst kursywny*, `code`, i [link](https://example.com) wszystko razem.

> **Uwaga:** To jest **uwaga** w formacie pogrubionym z *tekstem kursywnym* i `code`.

1. **Pierwszy** element z *tekstem kursywnym*
2. *Drugi* element z **tekstem pogrubionym**
3. `Third` element z [linkiem](⟦PROT

