import App from './App.jsx';
import React from 'react';
import { createRoot } from 'react-dom/client';

frappe.provide('traffictech');

traffictech.DocScanner = class DocScanner {
    constructor({ page, wrapper, form, liveDetection, onImagesUploaded }) {
        this.$wrapper = $(wrapper);
        this.page = page;
        this.form = form;
        this.onImagesUploaded = onImagesUploaded;
        this.liveDetection = liveDetection;

        this.init();
    }

    init() {
        this.setup_app();
    }

    setup_app() {
        const $container = $('<div>');
        $container.appendTo(this.$wrapper);

        $('.page-head').remove();

        const root = createRoot($container.get(0));
        root.render(
            <App form={this.form} liveDetection={this.liveDetection} onImagesUploaded={this.onImagesUploaded} />
        );
    }
};
