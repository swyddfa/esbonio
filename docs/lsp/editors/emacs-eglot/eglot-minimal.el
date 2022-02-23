;;; eglot-minimal.el --- Minimal exmaple config for using Esbonio with Eglot

;;; Commentary:
;;
;; To try this config:
;;
;; 1. Activate the virtualenv you use to build your Sphinx documentation.
;;
;;    $ source .env/bin/activate
;;
;; 2. Install the Esbonio language server.
;;
;;    (.env) $ pip install esbonio
;;
;; 3. Run the following command from a terminal in the folder where you have
;;    saved this file ('eglot-minimal.el')
;;
;;    (.env) $ emacs -Q -l eglot-minimal.el
;;
;;; Code:
(require 'package)

;; Set the user's .emacs.d directory to something else so that we don't
;; pollute their config.
(setq user-init-file load-file-name)
(setq user-emacs-directory (file-name-directory user-init-file))
(setq package-user-dir (locate-user-emacs-file "elpa"))

;; Write customize settings to a separate file.
(setq custom-file (concat user-emacs-directory "custom.el"))
(load custom-file 'noerror)

;; Ensure that the `eglot' package is installed.
(package-initialize)
(unless (package-installed-p 'eglot)
  (package-refresh-contents)
  (package-install 'eglot))

;; Tell `eglot' about the esbonio languge server and to start it when opening rst
;; files.
(require 'eglot)
(add-to-list 'eglot-server-programs
             `(rst-mode . (,(executable-find "python3") "-m" "esbonio")))
(add-hook 'rst-mode-hook 'eglot-ensure)

;; Setup some keybindings
(require 'rst)
(define-key rst-mode-map (kbd "C-M-i") 'completion-at-point)
