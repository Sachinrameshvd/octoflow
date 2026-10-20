/** Cinematic Guided Tour HUD & Story Player for Octopus Connectome.
 * Displays chapter narrative, biological microcircuit flow, and playback controls with Apple VisionOS styling.
 */

import type { StoryTourManager, TourChapter } from '../core/story-tour';
import { ICONS } from './icons';

export class TourHUD {
  private container: HTMLElement;
  private tourManager: StoryTourManager;

  public onExitTour?: () => void;

  constructor(tourManager: StoryTourManager, containerId: string = 'tour-hud-container') {
    this.tourManager = tourManager;
    let el = document.getElementById(containerId);
    if (!el) {
      el = document.createElement('div');
      el.id = containerId;
      el.className = 'hidden';
      const appContainer = document.getElementById('app-container');
      if (appContainer) {
        appContainer.appendChild(el);
      } else {
        document.body.appendChild(el);
      }
    }
    this.container = el;

    this.tourManager.onChapterChange = (chapter, index, total) => {
      this.render(chapter, index, total);
    };

    this.tourManager.onTimeUpdate = (_elapsed, _duration, percent) => {
      const bar = this.container.querySelector<HTMLElement>('#tour-progress-fill');
      if (bar) {
        bar.style.width = `${Math.min(100, Math.max(0, percent * 100))}%`;
      }
    };

    this.tourManager.onTourEnd = () => {
      this.hide();
      if (this.onExitTour) this.onExitTour();
    };
  }

  public show() {
    this.container.classList.remove('hidden');
    const chapter = this.tourManager.getCurrentChapter();
    this.render(chapter, this.tourManager.currentChapterIndex, this.tourManager.chapters.length);
  }

  public hide() {
    this.container.classList.add('hidden');
  }

  public render(chapter: TourChapter, index: number, total: number) {
    if (!chapter) return;

    const isPaused = this.tourManager.isTourPaused();
    const isLastChapter = index === total - 1;

    this.container.innerHTML = `
      <div class="tour-overlay-card glass-panel">
        <!-- Progress Bar at Top -->
        <div class="tour-progress-track">
          <div id="tour-progress-fill" class="tour-progress-fill"></div>
        </div>

        <!-- Header -->
        <div class="tour-header" style="cursor: grab;">
          <div class="tour-badge-row">
            <span class="window-drag-icon">${ICONS.dragGrip(14, 'rgba(255,255,255,0.6)')}</span>
            <span class="tour-badge">CHAPTER ${chapter.number} OF ${total}</span>
            <span class="tour-category-tag">${chapter.category}</span>
          </div>
          <button id="btn-tour-close" class="btn-tour-close" title="Exit Tour">
            ${ICONS.closeCross(12, '#cbd5e1')}
          </button>
        </div>

        <div class="tour-title-block">
          <h2 class="tour-title">${chapter.title}</h2>
          <p class="tour-subtitle">${chapter.subtitle}</p>
        </div>

        <!-- Key Scientific Insight Callout -->
        <div class="tour-key-concept">
          <span class="concept-icon">${ICONS.concept(16, '#fab387')}</span>
          <span class="concept-text">${chapter.keyConcept}</span>
        </div>

        <!-- Step-by-Step Microcircuit Flowchart -->
        <div class="tour-flow-container">
          <div class="tour-flow-title">NEURAL SIGNAL PATHWAY</div>
          <div class="tour-flow-steps">
            ${chapter.flowSteps
              .map(
                (s, i) => `
              <div class="flow-step flow-${s.type}">
                <span class="flow-step-num">${i + 1}</span>
                <span class="flow-step-name">${s.step}</span>
              </div>
              ${i < chapter.flowSteps.length - 1 ? `<span class="flow-arrow">${ICONS.flowArrow(10, 'rgba(255,255,255,0.4)')}</span>` : ''}
            `
              )
              .join('')}
          </div>
        </div>

        <!-- Main Narrative Description -->
        <div class="tour-narrative">
          ${chapter.narration.map((p) => `<p>${p}</p>`).join('')}
        </div>

        <!-- Chapter Jump Dots -->
        <div class="tour-chapter-dots">
          ${this.tourManager.chapters
            .map(
              (c, i) => `
            <button class="btn-chapter-dot ${i === index ? 'active' : ''}" data-chapter="${i}" title="${c.title}">
              <span class="dot-num">${i + 1}</span>
            </button>
          `
            )
            .join('')}
        </div>

        <!-- Playback Navigation Bar -->
        <div class="tour-playback-controls">
          <button id="btn-tour-prev" class="btn-tour-nav" ${index === 0 ? 'disabled' : ''}>
            ${ICONS.stepPrev(11, index === 0 ? 'rgba(255,255,255,0.3)' : '#ffffff')}
            <span>Prev</span>
          </button>
          
          <button id="btn-tour-playpause" class="btn-tour-playpause ${isPaused ? 'paused' : ''}">
            <span class="btn-tour-icon">${isPaused ? ICONS.play(11, '#ffffff') : ICONS.pause(11, '#ffffff')}</span>
            <span class="btn-tour-text">${isPaused ? 'Resume' : 'Pause'}</span>
          </button>

          <button id="btn-tour-next" class="btn-tour-nav">
            <span>${isLastChapter ? 'Finish' : 'Next'}</span>
            ${isLastChapter ? ICONS.finishFlag(12, '#34d399') : ICONS.stepNext(11, '#ffffff')}
          </button>

          <div class="tour-speed-selector">
            <button class="btn-speed active" data-speed="1.0">1.0x</button>
            <button class="btn-speed" data-speed="1.5">1.5x</button>
            <button class="btn-speed" data-speed="2.0">2.0x</button>
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  private bindEvents() {
    // Close / Exit
    const btnClose = this.container.querySelector('#btn-tour-close');
    if (btnClose) {
      btnClose.addEventListener('click', () => {
        this.tourManager.stopTour();
        this.hide();
        if (this.onExitTour) this.onExitTour();
      });
    }

    // Play / Pause
    const btnPlayPause = this.container.querySelector('#btn-tour-playpause');
    if (btnPlayPause) {
      btnPlayPause.addEventListener('click', () => {
        const isPaused = this.tourManager.togglePlayPause();
        const iconSpan = btnPlayPause.querySelector('.btn-tour-icon');
        const textSpan = btnPlayPause.querySelector('.btn-tour-text');
        if (iconSpan) {
          iconSpan.innerHTML = isPaused ? ICONS.play(11, '#ffffff') : ICONS.pause(11, '#ffffff');
        }
        if (textSpan) {
          textSpan.textContent = isPaused ? 'Resume' : 'Pause';
        }
        btnPlayPause.classList.toggle('paused', isPaused);
      });
    }

    // Prev
    const btnPrev = this.container.querySelector('#btn-tour-prev');
    if (btnPrev) {
      btnPrev.addEventListener('click', () => {
        this.tourManager.prevChapter();
      });
    }

    // Next
    const btnNext = this.container.querySelector('#btn-tour-next');
    if (btnNext) {
      btnNext.addEventListener('click', () => {
        this.tourManager.nextChapter();
      });
    }

    // Chapter Dots
    this.container.querySelectorAll('.btn-chapter-dot').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const target = e.currentTarget as HTMLElement;
        const chapIdx = parseInt(target.getAttribute('data-chapter') || '0', 10);
        this.tourManager.jumpToChapter(chapIdx);
      });
    });

    // Speed Selector
    this.container.querySelectorAll('.btn-speed').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const target = e.currentTarget as HTMLElement;
        const speed = parseFloat(target.getAttribute('data-speed') || '1.0');
        this.tourManager.setSpeed(speed);
        this.container.querySelectorAll('.btn-speed').forEach((b) => b.classList.remove('active'));
        target.classList.add('active');
      });
    });
  }
}
