/**
 * Lightweight mock DOM & Web APIs for Vitest running in node environments.
 * Provides zero-dependency DOM simulation for accessibility tests.
 */

export class MockElement {
  public tagName: string;
  public id: string = '';
  public className: string = '';
  public style: Record<string, string> = {};
  public attributes: Map<string, string> = new Map();
  public children: MockElement[] = [];
  public parentNode: MockElement | null = null;
  public listeners: Map<string, ((...args: any[]) => any)[]> = new Map();
  private _innerHTML: string = '';
  private _textContent: string = '';

  constructor(tagName: string) {
    this.tagName = tagName.toUpperCase();
  }

  public get innerHTML(): string {
    return this._innerHTML;
  }

  public set innerHTML(val: string) {
    this._innerHTML = val;
    this.children = parseHTML(val);
    for (const child of this.children) {
      child.parentNode = this;
    }
    this._textContent = this.children.length > 0
      ? this.children.map((c) => c.textContent).join(' ')
      : val.replace(/<[^>]*>/g, ' ');
  }

  public get textContent(): string {
    if (this.children.length > 0) {
      return this.children.map((c) => c.textContent).join(' ');
    }
    return this._textContent;
  }

  public set textContent(val: string) {
    this._textContent = val;
    this._innerHTML = val;
    this.children = [];
  }

  public setAttribute(name: string, value: string): void {
    this.attributes.set(name, String(value));
    if (name === 'id') this.id = value;
    if (name === 'class') this.className = value;
  }

  public getAttribute(name: string): string | null {
    return this.attributes.get(name) ?? null;
  }

  public hasAttribute(name: string): boolean {
    return this.attributes.has(name);
  }

  public removeAttribute(name: string): void {
    this.attributes.delete(name);
  }

  public appendChild(child: MockElement): MockElement {
    child.parentNode = this;
    this.children.push(child);
    return child;
  }

  public removeChild(child: MockElement): MockElement {
    const idx = this.children.indexOf(child);
    if (idx !== -1) {
      this.children.splice(idx, 1);
      child.parentNode = null;
    }
    return child;
  }

  public insertBefore(newChild: MockElement, _refChild: MockElement): MockElement {
    newChild.parentNode = this;
    this.children.unshift(newChild);
    return newChild;
  }

  public get firstChild(): MockElement | null {
    return this.children[0] ?? null;
  }

  public get lastChild(): MockElement | null {
    return this.children[this.children.length - 1] ?? null;
  }

  public querySelector(selector: string): MockElement | null {
    const all = this.querySelectorAll(selector);
    return all[0] ?? null;
  }

  public querySelectorAll(selector: string): MockElement[] {
    const matched: MockElement[] = [];
    const cleanSel = selector.trim();

    const search = (node: MockElement) => {
      if (cleanSel.startsWith('#')) {
        const id = cleanSel.slice(1);
        if (node.id === id) matched.push(node);
      } else if (cleanSel.startsWith('.')) {
        const cls = cleanSel.slice(1);
        if (node.className.split(' ').includes(cls)) matched.push(node);
      } else {
        if (node.tagName === cleanSel.toUpperCase()) matched.push(node);
      }
      for (const child of node.children) {
        search(child);
      }
    };

    for (const child of this.children) {
      search(child);
    }
    return matched;
  }

  public classList = {
    add: (c: string) => {
      const parts = this.className.split(' ').filter(Boolean);
      if (!parts.includes(c)) parts.push(c);
      this.className = parts.join(' ');
    },
    remove: (c: string) => {
      const parts = this.className.split(' ').filter((p) => p !== c);
      this.className = parts.join(' ');
    },
    toggle: (c: string, force?: boolean) => {
      const parts = this.className.split(' ').filter(Boolean);
      const exists = parts.includes(c);
      const shouldHave = force !== undefined ? force : !exists;
      if (shouldHave) {
        if (!exists) parts.push(c);
      } else {
        const idx = parts.indexOf(c);
        if (idx !== -1) parts.splice(idx, 1);
      }
      this.className = parts.join(' ');
      return shouldHave;
    },
    contains: (c: string) => this.className.split(' ').includes(c),
  };

  public addEventListener(event: string, fn: (...args: any[]) => any): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(fn);
  }

  public dispatchEvent(event: { type: string; [key: string]: any }): boolean {
    const list = this.listeners.get(event.type) || [];
    for (const fn of list) {
      fn(event);
    }
    return true;
  }

  public click(): void {
    this.dispatchEvent({ type: 'click' });
  }

  public focus(): void {}
}

export function parseHTML(html: string): MockElement[] {
  const cleanHtml = html.replace(/<!--[\s\S]*?-->/g, '');
  const root = new MockElement('root');
  const stack: MockElement[] = [root];
  const tagRegex = /<(\/)?([a-zA-Z0-9_-]+)([^>]*)>|([^<]+)/g;
  let match: RegExpExecArray | null;

  while ((match = tagRegex.exec(cleanHtml)) !== null) {
    const isClosing = match[1] === '/';
    const tagName = match[2];
    const attrString = match[3];
    const text = match[4];

    if (text) {
      if (text.trim()) {
        const top = stack[stack.length - 1];
        top.textContent = (top.textContent ? top.textContent + ' ' : '') + text.trim();
      }
      continue;
    }

    if (isClosing) {
      if (stack.length > 1 && stack[stack.length - 1].tagName.toLowerCase() === tagName.toLowerCase()) {
        stack.pop();
      }
    } else {
      const el = new MockElement(tagName);
      if (attrString) {
        const attrRegex = /([a-zA-Z0-9_-]+)(?:="([^"]*)")?/g;
        let attrMatch: RegExpExecArray | null;
        while ((attrMatch = attrRegex.exec(attrString)) !== null) {
          const k = attrMatch[1];
          const v = attrMatch[2] !== undefined ? attrMatch[2] : '';
          el.setAttribute(k, v);
        }
      }
      stack[stack.length - 1].appendChild(el);

      const voidTags = [
        'area', 'base', 'br', 'col', 'embed', 'hr', 'img',
        'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'
      ];
      if (!voidTags.includes(tagName.toLowerCase()) && !attrString.endsWith('/')) {
        stack.push(el);
      }
    }
  }

  return root.children;
}

export class MockLocalStorage {
  private store: Map<string, string> = new Map();

  public getItem(key: string): string | null {
    return this.store.get(key) ?? null;
  }

  public setItem(key: string, val: string): void {
    this.store.set(key, String(val));
  }

  public removeItem(key: string): void {
    this.store.delete(key);
  }

  public clear(): void {
    this.store.clear();
  }

  public get length(): number {
    return this.store.size;
  }
}

export function setupMockEnvironment() {
  const root = new MockElement('html');
  const body = new MockElement('body');
  root.appendChild(body);

  const storage = new MockLocalStorage();
  const elementsById = new Map<string, MockElement>();

  const doc = {
    documentElement: root,
    body: body,
    createElement: (tag: string) => new MockElement(tag),
    getElementById: (id: string) => {
      if (elementsById.has(id)) return elementsById.get(id)!;
      return root.querySelector(`#${id}`) || body.querySelector(`#${id}`);
    },
    registerElement: (el: MockElement) => {
      if (el.id) elementsById.set(el.id, el);
    },
  };

  const winListeners = new Map<string, ((...args: any[]) => any)[]>();
  const win = {
    document: doc,
    localStorage: storage,
    addEventListener: (event: string, fn: (...args: any[]) => any) => {
      const arr = winListeners.get(event) || [];
      arr.push(fn);
      winListeners.set(event, arr);
    },
    removeEventListener: (event: string, fn: (...args: any[]) => any) => {
      const arr = winListeners.get(event) || [];
      winListeners.set(event, arr.filter((f) => f !== fn));
    },
    dispatchEvent: (event: string, data?: any) => {
      const arr = winListeners.get(event) || [];
      arr.forEach((f) => f(data));
      return true;
    },
    matchMedia: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => true,
    }),
    speechSynthesis: {
      speak: () => {},
      cancel: () => {},
      getVoices: () => [],
      onvoiceschanged: null,
    },
    SpeechSynthesisUtterance: class {
      text: string;
      constructor(text: string) {
        this.text = text;
      }
    },
    setInterval: (fn: (...args: any[]) => any, ms: number) => setInterval(fn, ms),
    clearInterval: (id: any) => clearInterval(id),
    setTimeout: (fn: (...args: any[]) => any, ms: number) => setTimeout(fn, ms),
    clearTimeout: (id: any) => clearTimeout(id),
  };

  (globalThis as any).window = win;
  (globalThis as any).document = doc;
  (globalThis as any).localStorage = storage;

  return { root, body, storage, doc, win };
}
