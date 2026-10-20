/** Floating Window Manager for Octopus Connectome 3D Workspace.
 * Enables free dragging, corner resizing, roll-up minimize/restore, z-index focus, and layout persistence.
 */

import { ICONS } from './icons';

export interface WindowLayoutState {
  x: number;
  y: number;
  width?: number;
  height?: number;
  minimized?: boolean;
}

export interface ManagedWindowConfig {
  id: string;
  element: HTMLElement;
  title: string;
  defaultPosition: {
    left?: number;
    right?: number;
    top?: number;
    bottom?: number;
  };
  defaultDimensions: {
    width: number;
    height?: number;
    maxHeight?: number;
  };
  minWidth?: number;
  maxWidth?: number;
  minHeight?: number;
  maxHeight?: number;
  handleSelector?: string;
}

const STORAGE_KEY = 'octopus_workspace_layout_v2';

export class WindowManager {
  private windows: Map<string, ManagedWindowConfig> = new Map();
  private zIndexCounter = 35;
  private activeDrag: {
    id: string;
    startX: number;
    startY: number;
    initialLeft: number;
    initialTop: number;
    element: HTMLElement;
  } | null = null;

  private activeResize: {
    id: string;
    startX: number;
    startY: number;
    initialWidth: number;
    initialHeight: number;
    element: HTMLElement;
  } | null = null;

  constructor() {
    this.setupGlobalListeners();
  }

  public registerWindow(config: ManagedWindowConfig) {
    this.windows.set(config.id, config);
    const el = config.element;

    el.classList.add('floating-window');
    el.setAttribute('data-window-id', config.id);

    // Ensure resize handle exists
    if (!el.querySelector('.window-resize-gripper')) {
      const gripper = document.createElement('div');
      gripper.className = 'window-resize-gripper';
      gripper.title = 'Drag to resize window width & height';
      gripper.innerHTML = `
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M8 2L2 8M9 5L5 9M9 8L8 9" stroke="rgba(255,255,255,0.45)" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
      `;
      el.appendChild(gripper);
    }

    // Bring to front on click
    el.addEventListener('pointerdown', () => {
      this.bringToFront(el);
    });

    // Restore saved state or default
    this.applyWindowLayout(config);
  }

  public bringToFront(el: HTMLElement) {
    this.zIndexCounter += 1;
    el.style.zIndex = `${this.zIndexCounter}`;
  }

  public toggleMinimize(id: string) {
    const config = this.windows.get(id);
    if (!config) return;
    const el = config.element;
    const isMinimized = el.classList.toggle('window-minimized');

    // Update minimize button icon if present
    const minBtn = el.querySelector<HTMLButtonElement>('.btn-window-minimize');
    if (minBtn) {
      minBtn.innerHTML = isMinimized ? ICONS.maximize(11, '#ffffff') : ICONS.minimize(11, '#ffffff');
      minBtn.title = isMinimized ? 'Expand Window' : 'Minimize Window';
    }

    this.saveState();
  }

  public resetAll() {
    localStorage.removeItem(STORAGE_KEY);
    this.windows.forEach((config) => {
      const el = config.element;
      el.classList.remove('window-minimized');
      el.style.removeProperty('transform');

      // Reset minimize button icon
      const minBtn = el.querySelector<HTMLButtonElement>('.btn-window-minimize');
      if (minBtn) {
        minBtn.innerHTML = ICONS.minimize(11, '#ffffff');
        minBtn.title = 'Minimize Window';
      }

      this.applyDefaultPosition(config);
    });
  }

  private applyDefaultPosition(config: ManagedWindowConfig) {
    const el = config.element;
    const { left, right, top, bottom } = config.defaultPosition;
    const { width, height, maxHeight } = config.defaultDimensions;

    el.style.position = 'absolute';
    el.style.left = left !== undefined ? `${left}px` : 'auto';
    el.style.right = right !== undefined ? `${right}px` : 'auto';
    el.style.top = top !== undefined ? `${top}px` : 'auto';
    el.style.bottom = bottom !== undefined ? `${bottom}px` : 'auto';

    el.style.width = `${width}px`;
    if (height) {
      el.style.height = `${height}px`;
    } else {
      el.style.height = 'auto';
    }

    if (maxHeight) {
      el.style.maxHeight = `${maxHeight}px`;
    }
  }

  private applyWindowLayout(config: ManagedWindowConfig) {
    const saved = this.loadState();
    const state = saved[config.id];

    if (!state) {
      this.applyDefaultPosition(config);
      return;
    }

    const el = config.element;
    el.style.position = 'absolute';
    el.style.margin = '0';
    el.style.right = 'auto';
    el.style.bottom = 'auto';

    // Clamp coordinates within visible screen
    const maxX = Math.max(20, window.innerWidth - 80);
    const maxY = Math.max(20, window.innerHeight - 80);
    const clampedX = Math.min(Math.max(10, state.x), maxX);
    const clampedY = Math.min(Math.max(10, state.y), maxY);

    el.style.left = `${clampedX}px`;
    el.style.top = `${clampedY}px`;

    if (state.width) {
      const minW = config.minWidth || 240;
      const maxW = config.maxWidth || window.innerWidth - 40;
      el.style.width = `${Math.min(Math.max(minW, state.width), maxW)}px`;
    } else {
      el.style.width = `${config.defaultDimensions.width}px`;
    }

    if (state.height) {
      const minH = config.minHeight || 120;
      const maxH = config.maxHeight || window.innerHeight - 40;
      const h = Math.min(Math.max(minH, state.height), maxH);
      el.style.height = `${h}px`;
      el.style.maxHeight = `${h}px`;
    }

    if (state.minimized) {
      el.classList.add('window-minimized');
      const minBtn = el.querySelector<HTMLButtonElement>('.btn-window-minimize');
      if (minBtn) {
        minBtn.innerHTML = ICONS.maximize(11, '#ffffff');
        minBtn.title = 'Expand Window';
      }
    }
  }

  private setupGlobalListeners() {
    // 1. Pointer Down delegation for dragging handles & resize grippers
    document.addEventListener('pointerdown', (e: PointerEvent) => {
      const target = e.target as HTMLElement;
      if (!target) return;

      // Check if clicking resize gripper
      const gripper = target.closest('.window-resize-gripper') as HTMLElement;
      if (gripper) {
        const windowEl = gripper.closest('.floating-window') as HTMLElement;
        if (windowEl) {
          const windowId = windowEl.getAttribute('data-window-id');
          if (windowId && this.windows.has(windowId)) {
            e.preventDefault();
            this.bringToFront(windowEl);
            const rect = windowEl.getBoundingClientRect();
            this.activeResize = {
              id: windowId,
              startX: e.clientX,
              startY: e.clientY,
              initialWidth: rect.width,
              initialHeight: rect.height,
              element: windowEl,
            };
            document.body.classList.add('is-resizing-window');
            return;
          }
        }
      }

      // Check if clicking minimize button
      const minBtn = target.closest('.btn-window-minimize');
      if (minBtn) {
        const windowEl = minBtn.closest('.floating-window') as HTMLElement;
        const windowId = windowEl?.getAttribute('data-window-id');
        if (windowId) {
          e.preventDefault();
          e.stopPropagation();
          this.toggleMinimize(windowId);
          return;
        }
      }

      // Ignore interactive input / button / slider clicks inside headers
      if (target.closest('button, input, select, a') && !target.closest('.window-drag-handle, .window-titlebar')) {
        return;
      }

      // Check if clicking header or drag handle
      const handle = target.closest('.window-titlebar, .window-drag-handle, .signal-panel-header, .inspector-header, .tour-header') as HTMLElement;
      if (handle) {
        // If clicking a button inside header (like close button or interactive toggle), ignore drag
        if (target.closest('button:not(.window-drag-btn), input, select')) {
          return;
        }

        const windowEl = handle.closest('.floating-window') as HTMLElement;
        if (!windowEl) return;
        const windowId = windowEl.getAttribute('data-window-id');
        if (!windowId || !this.windows.has(windowId)) return;

        e.preventDefault();
        this.bringToFront(windowEl);
        const rect = windowEl.getBoundingClientRect();

        this.activeDrag = {
          id: windowId,
          startX: e.clientX,
          startY: e.clientY,
          initialLeft: rect.left,
          initialTop: rect.top,
          element: windowEl,
        };
        document.body.classList.add('is-dragging-window');
      }
    });

    // 2. Pointer Move for active dragging or resizing
    document.addEventListener('pointermove', (e: PointerEvent) => {
      if (this.activeDrag) {
        e.preventDefault();
        const { startX, startY, initialLeft, initialTop, element } = this.activeDrag;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;

        let newLeft = initialLeft + dx;
        let newTop = initialTop + dy;

        // Viewport boundary clamp
        const minX = 4;
        const maxX = window.innerWidth - 60;
        const minY = 4;
        const maxY = window.innerHeight - 50;

        newLeft = Math.max(minX, Math.min(newLeft, maxX));
        newTop = Math.max(minY, Math.min(newTop, maxY));

        element.style.margin = '0';
        element.style.transform = 'none';
        element.style.right = 'auto';
        element.style.bottom = 'auto';
        element.style.left = `${newLeft}px`;
        element.style.top = `${newTop}px`;
        return;
      }

      if (this.activeResize) {
        e.preventDefault();
        const { id, startX, startY, initialWidth, initialHeight, element } = this.activeResize;
        const config = this.windows.get(id);
        if (!config) return;

        const dx = e.clientX - startX;
        const dy = e.clientY - startY;

        const minW = config.minWidth || 220;
        const maxW = config.maxWidth || window.innerWidth - 20;
        const minH = config.minHeight || 120;
        const maxH = config.maxHeight || window.innerHeight - 20;

        const newWidth = Math.max(minW, Math.min(initialWidth + dx, maxW));
        const newHeight = Math.max(minH, Math.min(initialHeight + dy, maxH));

        element.style.width = `${newWidth}px`;
        element.style.height = `${newHeight}px`;
        element.style.maxHeight = `${newHeight}px`;
      }
    });

    // 3. Pointer Up to finish drag or resize
    document.addEventListener('pointerup', () => {
      if (this.activeDrag) {
        this.activeDrag = null;
        document.body.classList.remove('is-dragging-window');
        this.saveState();
      }
      if (this.activeResize) {
        this.activeResize = null;
        document.body.classList.remove('is-resizing-window');
        this.saveState();
      }
    });

    // 4. Double click titlebar to minimize / expand
    document.addEventListener('dblclick', (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target || target.closest('button, input, select')) return;
      const handle = target.closest('.window-titlebar, .signal-panel-header, .inspector-header, .tour-header');
      if (handle) {
        const windowEl = handle.closest('.floating-window') as HTMLElement;
        const windowId = windowEl?.getAttribute('data-window-id');
        if (windowId) {
          this.toggleMinimize(windowId);
        }
      }
    });
  }

  private saveState() {
    const state: Record<string, WindowLayoutState> = {};
    this.windows.forEach((_config, id) => {
      const el = document.getElementById(id);
      if (!el) return;
      const rect = el.getBoundingClientRect();
      state[id] = {
        x: Math.round(rect.left),
        y: Math.round(rect.top),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        minimized: el.classList.contains('window-minimized'),
      };
    });
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // Ignore quota error
    }
  }

  private loadState(): Record<string, WindowLayoutState> {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  }
}
