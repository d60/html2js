### Examples

```python
html = '''
<div class="container">
    <p class="list-title">Number List:</p>
    <ul class="number-list">
        <li>1</li>
        <li>2</li>
        <li>3</li>
    </ul>
</div>
'''

js = convert_as_function(html, 'createDiv')
print(js)
```

Output:
```js
function createDiv() {
    const div1 = document.createElement("div");
    div1.className = "container";
    const p1 = document.createElement("p");
    p1.className = "list-title";
    const text1 = document.createTextNode(`Number List:`);
    p1.appendChild(text1);
    const ul1 = document.createElement("ul");
    ul1.className = "number-list";
    const li1 = document.createElement("li");
    const text2 = document.createTextNode(`1`);
    li1.appendChild(text2);
    const li2 = document.createElement("li");
    const text3 = document.createTextNode(`2`);
    li2.appendChild(text3);
    const li3 = document.createElement("li");
    const text4 = document.createTextNode(`3`);
    li3.appendChild(text4);
    ul1.appendChild(li1);
    ul1.appendChild(li2);
    ul1.appendChild(li3);
    div1.appendChild(p1);
    div1.appendChild(ul1);
    return div1;
}
```
