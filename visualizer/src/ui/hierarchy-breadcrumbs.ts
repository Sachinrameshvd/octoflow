/** Hierarchical Breadcrumb Navigation Bar for Progressive Connectome Traversal. */

import type { HierarchyLevel } from '../core/camera-controller';

export interface BreadcrumbItem {
  level: HierarchyLevel;
  label: string;
  subLabel?: string;
  onClick: () => void;
}

export class HierarchyBreadcrumbs {
  private container: HTMLElement;
  private items: BreadcrumbItem[] = [];

  constructor(containerId: string = 'hierarchy-breadcrumbs') {
    this.container = document.getElementById(containerId) || document.body;
  }

  public setPath(items: BreadcrumbItem[]) {
    this.items = items;
    this.render();
  }

  private render() {
    this.container.innerHTML = `
      <div class="breadcrumb-bar">
        <span class="breadcrumb-label">ANATOMICAL DEPTH:</span>
        ${this.items
          .map(
            (item, idx) => `
          <button class="breadcrumb-btn ${idx === this.items.length - 1 ? 'active' : ''}" data-index="${idx}">
            ${item.label}
          </button>
          ${idx < this.items.length - 1 ? '<span class="breadcrumb-sep">/</span>' : ''}
        `
          )
          .join('')}
      </div>
    `;

    this.container.querySelectorAll('.breadcrumb-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const target = e.currentTarget as HTMLElement;
        const idx = parseInt(target.getAttribute('data-index') || '0', 10);
        const item = this.items[idx];
        if (item) {
          item.onClick();
        }
      });
    });
  }
}
