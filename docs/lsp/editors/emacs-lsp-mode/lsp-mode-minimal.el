;;; lsp-mode-minimal.el --- Minimal exmaple config for using Esbonio with LSP Mode

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
;; 3. Save the 'lsp-mode-minimal.el' config to a folder of your choosing.
;;
;; 4. Run the following command from a terminal in the folder where you have
;;    saved 'lsp-mode-minimal.el'
;;
;;    emacs -Q -l lsp-mode-minimal.el
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

;; Enable the MELPA repository
(setq package-archives '(("elpa"  . "https://elpa.gnu.org/packages/")
                         ("melpa" . "https://melpa.org/packages/")))

;; Ensure that the `lsp-mode' package is installed.
(package-initialize)
(unless (package-installed-p 'lsp-mode)
  (package-refresh-contents)
  (package-install 'lsp-mode))

;; Register the Esbonio language server with lsp-mode
(require 'lsp-mode)

(add-to-list 'lsp-language-id-configuration '(rst-mode . "rst"))
(lsp-register-client
 (make-lsp-client :new-connection
		  (lsp-stdio-connection
                   `(,(executable-find "python3") "-m" "esbonio"))
                  :activation-fn (lsp-activate-on "rst")
                  :server-id 'esbonio))

(add-hook 'rst-mode-hook 'lsp)

;; Setup some keybindings
(require 'rst)
(define-key rst-mode-map (kbd "C-M-i") 'completion-at-point)
