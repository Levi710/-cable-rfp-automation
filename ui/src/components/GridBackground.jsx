import React, { useEffect, useRef } from 'react';
import anime from 'animejs';

const GridBackground = () => {
    const gridRef = useRef(null);

    useEffect(() => {
        // Create grid items
        const gridContainer = gridRef.current;
        if (!gridContainer) return;

        // Clear previous content
        gridContainer.innerHTML = '';

        const w = gridContainer.clientWidth;
        const h = gridContainer.clientHeight;
        // Calculate number of columns and rows based on screen size
        // Smaller blocks for more density
        const size = 50;
        const cols = Math.ceil(w / size);
        const rows = Math.ceil(h / size);
        const total = cols * rows;

        for (let i = 0; i < total; i++) {
            const el = document.createElement('div');
            el.classList.add('grid-item');
            el.style.width = `${size}px`;
            el.style.height = `${size}px`;
            el.style.border = '1px solid #1f2937'; // tech-slate border
            el.style.boxSizing = 'border-box';
            el.style.opacity = '0.3';
            gridContainer.appendChild(el);
        }

        // Staggered animation
        anime({
            targets: '.grid-item',
            scale: [
                { value: .1, easing: 'easeOutSine', duration: 500 },
                { value: 1, easing: 'easeInOutQuad', duration: 1200 }
            ],
            delay: anime.stagger(200, { grid: [cols, rows], from: 'center' }),
            loop: true,
            direction: 'alternate'
        });

        // cleanup
        return () => {
            // anime.remove('.grid-item'); // sometimes tricky to cleanup global anime instances
        }

    }, []);

    return (
        <div
            ref={gridRef}
            className="fixed inset-0 z-0 flex flex-wrap"
            style={{ pointerEvents: 'none' }} // Ensure clicks pass through
        >
        </div>
    );
};

export default GridBackground;
