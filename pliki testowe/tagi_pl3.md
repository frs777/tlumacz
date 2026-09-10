# Plik Testowy Markdown

Ten plik zawiera różne znaczniki Markdown w celu przetestowania tłumaczenia.

## Nagłówki

### Nagłówek H3
#### Nagłówek H4
##### Nagłówek H5
###### Nagłówek H6

## Formatowanie tekstu

**Tekst pogrubiony** i *tekst kursywa* i ***tekst pogrubiony i kursywa*** i ~~tekst przekreślony~~ i `inline code`.

## Listy

### Lista nieuporządkowana
- Element 1
- Element 2
  - Podelement 2.1
  - Podelement 2.2
- Element 3

### Lista uporządkowana
1. Pierwszy element
2. Drugi element
   1. Podelement 2.1
   2. Podelement 2.2
3. Trzeci element

### Lista zadań
- [x] Ukończone zadanie
- [ ] Oczekujące zadanie
- [ ] Kolejne oczekujące zadanie

## Linki i obrazy

[Tekst linku](https://example.com "Tytuł")

![Tekst alternatywny](https://example.com/image.png "Tytuł obrazu")

## Cytowania

> To jest cytowanie.
> Może się rozciągać na wiele linii.
>
> > Wbudowane cytowanie.

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

| Lewy | Środkowy | Prawy |
|:-----|:------:|------:|
| L1   | C1     | R1    |
| L2   | C2     | R2    |

## Linie poziome


---
***

___

## HTML w Markdown

<div class="container">
  <p>To jest akapit w formacie HTML.</p>
  <ul>
    <li>Element listy HTML</li>
    <li>Element listy HTML</li>
  </ul>
</div>

## Znaky ucieczki

\*Nie kursywa\*

\# Nie jest nagłówkiem

\[Nie jest linkiem\]

## Przerwy w linii

Pierwsza linia
Druga linia (z dwoma spacjami na końcu)

Pierwsza linia\
Druga linia (z ukośnikiem)

## Przypisy

Ten tekst ma przypis[^1] i jeszcze jeden[^note].

[^1]: To jest pierwszy przypis.
[^note]: To jest przypis o nazwie.

## Listy definicji

Termin 1
: Definicja 1

Termin 2
: Definicja 2a
: Definicja 2b

## Matematyka (jeśli obsługiwane)

Matematyka w linii: $E = mc^2$

Matematyka w bloku:
$$
\int_{0}^{\infty} e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
$$

## Emoji i specjalne znaki

✅ Znacznik wyboru
❌ Znacznik krzyża
⚠️ Ostrzeżenie
 Notatka

Specjalne: © ® ™ € £ ¥

## Mieszane treści

Ten akapit ma **pogrubienie**, *kursywę*, `code` i [link](https://example.com) razem.

> **Uwaga:** To jest **uwaga** z *kursywą* i `code`.

1. **Pierwszy** element z *kursywą*
2. *Drugi* element z **pogrubieniem**
3. `Third` element z [linkiem](https://example.com)


