;;; lsp-mode-extended.el --- Extended exmaple config for using Esbonio with LSP Mode

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
;; 3. Save the 'lsp-mode-extended.el' config to a folder of your choosing.
;;
;; 4. Run the following command from a terminal in the folder where you have
;;    saved 'lsp-mode-extended.el'
;;
;;    emacs -Q -l lsp-mode-extended.el
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

;; Ensure that the `use-package' package is installed.
(package-initialize)
(unless (package-installed-p 'use-package)
  (package-refresh-contents)
  (package-install 'use-package))

;; Most important, ensure that lsp-mode is available and configured.
(use-package lsp-mode
  :ensure t
  :config
  (add-to-list 'lsp-language-id-configuration '(rst-mode . "rst"))
  (lsp-register-client
   (make-lsp-client :new-connection
		    (lsp-stdio-connection
                     `(,(executable-find "python3") "-m" "esbonio"))
                    :activation-fn (lsp-activate-on "rst")
                    :initialization-options (lambda () `((sphinx . ((confDir . "${workspaceRoot}")
                                                                    (srcDir . "${confDir}")))
                                                         (server . ((logLevel . "debug")))))
                    :server-id 'esbonio)))

(use-package rst
  :hook (rst-mode . lsp))

;; UI Tweaks
(scroll-bar-mode -1)
(tool-bar-mode -1)
(menu-bar-mode -1)
(global-display-line-numbers-mode 1)

(use-package company
  :ensure t
  :config
  (global-company-mode))

(use-package doom-themes
  :ensure t
  :config
  (setq doom-themes-enable-bold t
        doom-themes-enable-italic t)
  (load-theme 'doom-vibrant t))

(use-package doom-modeline
  :ensure t
  :init (doom-modeline-mode 1)
  :config
  (column-number-mode 1)
  (setq doom-modeline-buffer-file-name-style 'relative-to-project
        doom-modeline-buffer-modification-icon t
        doom-modeline-buffer-state-icon t
        doom-modeline-height 25
        doom-modeline-major-mode-icon t
        doom-modeline-major-mode-color-icont t
        doom-modeline-minor-modes nil))

(use-package solaire-mode
  :ensure t
  :init
  (solaire-global-mode))

(use-package treemacs
  :ensure t
  :init
  (treemacs)
  (treemacs-follow-mode))

(use-package yasnippet
  :ensure t
  :hook (lsp-mode . yas-minor-mode))
