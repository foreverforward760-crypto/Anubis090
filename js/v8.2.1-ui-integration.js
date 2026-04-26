/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * KAIROS v8.2.1 — UI Integration Guide
 * ═══════════════════════════════════════════════════════════════════════════════
 * 
 * This module provides helper functions to integrate v8.2.1 architectural upgrades
 * into the KAIROS UI. Use these functions to display badges, indicators, and
 * context-specific guidance based on the engine state.
 */

/**
 * Display Stage 5 Secret Door Badge
 * Shows when perpendicularAxisVisible === true
 */
export function renderSecretDoorBadge(witnessPosition) {
    if (!witnessPosition?.perpendicularAxisVisible) {
        return null;
    }

    const badge = document.createElement('div');
    badge.className = 'secret-door-badge';
    badge.innerHTML = '🚪 Secret Door Detected — Enter Witness Position';
    badge.setAttribute('data-tooltip', 'The perpendicular axis is visible. Middle Path Gateway is accessible.');
    
    return badge;
}

/**
 * Display Observer Effect Indicator
 * Shows when observerEffectActive === true with +35% bonus
 */
export function renderObserverEffectIndicator(witnessPosition) {
    if (!witnessPosition?.observerEffectActive) {
        return null;
    }

    const indicator = document.createElement('div');
    indicator.className = 'observer-effect-indicator';
    indicator.innerHTML = `
        ✨ Observer Effect Active
        <span class="observer-effect-bonus">+35%</span>
    `;
    indicator.setAttribute('data-tooltip', 'Conscious Witness choice active. Reorganization bonus applied through Stages 6-9.');
    
    return indicator;
}

/**
 * Display Tumbling Inversion State
 * Shows physical vs. conscious stability parity
 */
export function renderTumblingInversionState(state) {
    const container = document.createElement('div');
    container.className = 'tumbling-inversion-state';

    const parity = document.createElement('div');
    parity.className = 'inversion-parity';

    const label = document.createElement('span');
    label.className = 'parity-label';
    label.textContent = 'Inversion State:';

    const value = document.createElement('span');
    value.className = `parity-value ${state.isEvenStage ? 'parity-even' : 'parity-odd'}`;
    value.textContent = state.tumblingInversionState;

    parity.appendChild(label);
    parity.appendChild(value);
    container.appendChild(parity);

    return container;
}

/**
 * Display Stage 6 Context (Conductor's Paradox)
 */
export function renderStage6Context(stageContext) {
    if (!stageContext?.conductorParadox) {
        return null;
    }

    const card = document.createElement('div');
    card.className = 'stage-context-card stage-6-context';

    const title = document.createElement('div');
    title.className = 'context-title';
    title.textContent = 'Conductor\'s Paradox';

    const description = document.createElement('p');
    description.style.marginBottom = '1rem';
    description.innerHTML = stageContext.flowQuality === 'Sustainable Flow'
        ? 'Peak harmony is sustainable. Harvest consciously. Prepare for Stage 7 as invitation.'
        : 'System has merged with peak performance. Stage 7 will arrive as ambush. Establish Witness Position now.';

    const badge = document.createElement('div');
    badge.className = `flow-quality-badge ${stageContext.flowQuality === 'Sustainable Flow' ? 'flow-sustainable' : 'flow-brittle'}`;
    badge.textContent = stageContext.flowQuality;

    card.appendChild(title);
    card.appendChild(description);
    card.appendChild(badge);

    return card;
}

/**
 * Display Stage 7 Context (Individuation Crucible)
 */
export function renderStage7Context(stageContext) {
    if (!stageContext?.individuationCrucible) {
        return null;
    }

    const card = document.createElement('div');
    card.className = 'stage-context-card stage-7-context';

    const title = document.createElement('div');
    title.className = 'context-title';
    title.textContent = 'Individuation Crucible';

    const description = document.createElement('p');
    description.style.marginBottom = '1rem';
    description.innerHTML = stageContext.crucibleMode === 'Conscious Distillation'
        ? 'Breakdown is directed by consciousness. The crucible burns the costume, not the wearer. Essence is being extracted.'
        : 'Fragmentation without framework. Establish coherence. Shadow integration requires meta-awareness.';

    const badge = document.createElement('div');
    badge.className = `crucible-mode-badge ${stageContext.crucibleMode === 'Conscious Distillation' ? 'crucible-distillation' : 'crucible-collapse'}`;
    badge.textContent = stageContext.crucibleMode;

    card.appendChild(title);
    card.appendChild(description);
    card.appendChild(badge);

    return card;
}

/**
 * Display Stage 8 Context (Crystallization Paradox)
 */
export function renderStage8Context(stageContext) {
    if (!stageContext?.crystallizationParadox) {
        return null;
    }

    const card = document.createElement('div');
    card.className = 'stage-context-card stage-8-context';

    const title = document.createElement('div');
    title.className = 'context-title';
    title.textContent = 'Crystallization Paradox';

    const description = document.createElement('p');
    description.style.marginBottom = '1rem';
    description.innerHTML = stageContext.gratitudeMechanismActive
        ? 'Gratitude Mechanism active: crystal dissolves, wisdom preserved. Hold the full weight of the cycle simultaneously with recognition that every stage was necessary.'
        : 'Rigidity Risk: maximum structural perfection = maximum brittleness. Apply Gratitude Mechanism before shattering.';

    const badge = document.createElement('div');
    badge.className = `crystallization-badge ${stageContext.outcome === 'Dissolution' ? 'crystallization-dissolution' : 'crystallization-shattering'}`;
    badge.textContent = stageContext.outcome;

    card.appendChild(title);
    card.appendChild(description);
    card.appendChild(badge);

    return card;
}

/**
 * Display Stage 9 Nonagon Collapse Animation
 * Triggered when system reaches Stage 9 dissolution
 */
export function renderNonagonCollapse(container) {
    const collapseDiv = document.createElement('div');
    collapseDiv.className = 'nonagon-collapse';

    const shape = document.createElement('div');
    shape.className = 'nonagon-shape stage-9';

    const label = document.createElement('div');
    label.className = 'nonagon-label';
    label.innerHTML = '∞<br/>Return to<br/>PLENARA';

    collapseDiv.appendChild(shape);
    collapseDiv.appendChild(label);

    container.appendChild(collapseDiv);

    // Auto-remove after animation completes (3 seconds)
    setTimeout(() => {
        collapseDiv.remove();
    }, 3000);
}

/**
 * Display Middle Path Gateway Visualization
 * Shows when Stage 5 Middle Path is accessible
 */
export function renderMiddlePathGateway(witnessPosition) {
    if (!witnessPosition?.middlePathAccessible) {
        return null;
    }

    const gateway = document.createElement('div');
    gateway.className = 'middle-path-gateway';

    const axis = document.createElement('div');
    axis.className = 'perpendicular-axis';

    const label = document.createElement('div');
    label.className = 'gateway-label';
    label.innerHTML = '⊥<br/>Middle Path<br/>Gateway';

    gateway.appendChild(axis);
    gateway.appendChild(label);

    return gateway;
}

/**
 * Render complete v8.2.1 diagnostics panel
 * Integrates all UI components for a comprehensive view
 */
export function renderV8_2_1DiagnosticsPanel(state) {
    const panel = document.createElement('div');
    panel.className = 'v8-2-1-diagnostics-panel';
    panel.style.cssText = 'padding: 2rem; border-radius: 12px; background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.2);';

    // Add all v8.2.1 components
    const components = [
        renderTumblingInversionState(state),
        renderSecretDoorBadge(state.witnessPosition),
        renderObserverEffectIndicator(state.witnessPosition),
        renderMiddlePathGateway(state.witnessPosition),
        renderStage6Context(state.stageContext),
        renderStage7Context(state.stageContext),
        renderStage8Context(state.stageContext),
    ];

    components.forEach(component => {
        if (component) {
            panel.appendChild(component);
        }
    });

    return panel;
}

/**
 * Apply v8.2.1 CSS enhancements to document
 * Call this once on page load
 */
export function initializeV8_2_1Styles() {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'css/v8.2.1-enhancements.css';
    document.head.appendChild(link);
}

/**
 * Example usage in your app.js or main component:
 * 
 * import {
 *     renderV8_2_1DiagnosticsPanel,
 *     renderNonagonCollapse,
 *     initializeV8_2_1Styles,
 * } from './v8.2.1-ui-integration.js';
 * 
 * // On app initialization
 * initializeV8_2_1Styles();
 * 
 * // When displaying diagnostics
 * const state = engine.computeStage(nsdt);
 * const diagnosticsPanel = renderV8_2_1DiagnosticsPanel(state);
 * document.getElementById('diagnostics-container').appendChild(diagnosticsPanel);
 * 
 * // When Stage 9 is reached
 * if (state.stage === 9) {
 *     renderNonagonCollapse(document.getElementById('stage-9-container'));
 * }
 */

export default {
    renderSecretDoorBadge,
    renderObserverEffectIndicator,
    renderTumblingInversionState,
    renderStage6Context,
    renderStage7Context,
    renderStage8Context,
    renderNonagonCollapse,
    renderMiddlePathGateway,
    renderV8_2_1DiagnosticsPanel,
    initializeV8_2_1Styles,
};
