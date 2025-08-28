(use-modules (ice-9 format)
             (ice-9 textual-ports)
             (ice-9 rdelim))

(define *cogserver-connection* #f)
(define *cogserver-host* "localhost")
(define *cogserver-port* 17001)

(define (connect-to-cogserver)
  "Establish connection to CogServer via telnet"
  (catch 'system-error
    (lambda ()
      (let ((sock (socket PF_INET SOCK_STREAM 0)))
        (connect sock AF_INET (inet-aton *cogserver-host*) *cogserver-port*)
        (set! *cogserver-connection* sock)
        (display "🌉 Connected to CogServer\n")
        #t))
    (lambda (key . args)
      (display "⚠️ Could not connect to CogServer, using file-based fallback\n")
      #f)))

(define (send-to-cog form)
  "Send form to CogServer via active connection or file fallback"
  (display "📡 Sending to CogServer:\n")
  (write form)
  (newline)
  
  (cond
    ;; Try direct connection first
    (*cogserver-connection*
     (catch 'system-error
       (lambda ()
         (let ((command (format #f "~a\n" form)))
           (display command *cogserver-connection*)
           (force-output *cogserver-connection*)
           (let ((response (read-line *cogserver-connection*)))
             (format #t "🧠 CogServer response: ~a~%" response)
             response)))
       (lambda (key . args)
         (display "❌ Connection lost, falling back to file mode\n")
         (set! *cogserver-connection* #f)
         (send-to-cog-file form))))
    
    ;; Fallback to file-based communication
    (else
     (send-to-cog-file form))))

(define (send-to-cog-file form)
  "Send command via file-based interface for CogServer"
  (let* ((timestamp (current-time))
         (filename (format #f "/tmp/cogserver_commands/wolf_cmd_~a.scm" timestamp)))
    (call-with-output-file filename
      (lambda (port)
        (write form port)))
    (format #t "📁 Command saved to file: ~a~%" filename)
    form))

(define (cog-evaluate expr)
  "Evaluate expression in OpenCog AtomSpace"
  (let ((eval-form `(cog-evaluate! (ParseNode "evaluate" (ConceptNode ,expr)))))
    (send-to-cog eval-form)))

(define (wolf-to-atomspace data)
  "Convert Wolf symbolic data to AtomSpace atoms"
  (format #t "🔄 Converting Wolf data to AtomSpace: ~a~%" data)
  
  (cond
    ;; Handle symbolic expressions
    ((string? data)
     (let ((concept-form `(ConceptNode ,data)))
       (send-to-cog concept-form)
       concept-form))
    
    ;; Handle lists as inheritance links
    ((list? data)
     (let ((link-form `(InheritanceLink ,@data)))
       (send-to-cog link-form)
       link-form))
    
    ;; Handle numbers as number nodes
    ((number? data)
     (let ((number-form `(NumberNode ,(number->string data))))
       (send-to-cog number-form)
       number-form))
    
    ;; Default case
    (else
     (let ((concept-form `(ConceptNode ,(format #f "~a" data))))
       (send-to-cog concept-form)
       concept-form))))

(define (atomspace-to-wolf atoms)
  "Convert AtomSpace atoms to Wolf symbolic format"
  (format #t "🔄 Converting AtomSpace to Wolf format: ~a~%" atoms)
  
  (cond
    ;; Handle concept nodes
    ((and (list? atoms) (eq? (car atoms) 'ConceptNode))
     (cadr atoms))
    
    ;; Handle inheritance links
    ((and (list? atoms) (eq? (car atoms) 'InheritanceLink))
     (cdr atoms))
    
    ;; Handle evaluation links
    ((and (list? atoms) (eq? (car atoms) 'EvaluationLink))
     `(evaluation ,(cadr atoms) ,(caddr atoms)))
    
    ;; Default: return as-is
    (else atoms)))

(define (init-cog-bridge)
  "Initialize bridge between Wolf and OpenCog"
  (display "🌉 Initializing Wolf-to-Cog bridge...\n")
  
  ;; Try to connect to CogServer
  (if (connect-to-cogserver)
      (display "✅ CogServer connection established\n")
      (display "⚠️ Using file-based communication mode\n"))
  
  ;; Ensure command directory exists
  (system "mkdir -p /tmp/cogserver_commands")
  
  #t)

(define (close-cog-bridge)
  "Close bridge connection"
  (when *cogserver-connection*
    (close *cogserver-connection*)
    (set! *cogserver-connection* #f)
    (display "🔌 CogServer connection closed\n")))

;; Initialize the bridge
(init-cog-bridge)