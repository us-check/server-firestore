sequenceDiagram
    actor User
    participant Django as Django Backend (views.py)
    participant Services as Business Logic (services.py)
    participant Gemini as Google Gemini API
    participant Firestore as Google Cloud Firestore
    participant PubSub as Google Cloud Pub/Sub
    participant GCF as Cloud Function (generate_qr_pubsub)
    participant GCS as Google Cloud Storage

    title System-Wide Sequence Diagram

    alt AI Recommendation Flow
        User->>+Django: 1. POST /api/query/ with natural language query
        Django->>+Services: 2. process_query(query)
        Services->>+Gemini: 3. Analyze text for intent and keywords
        Gemini-->>-Services: 4. Return analysis
        Services->>+Firestore: 5. Query documents with keywords
        Firestore-->>-Services: 6. Return matching documents
        Services-->>-Django: 7. Return recommendation data
        Django-->>-User: 8. JSON response with recommendations
    else Asynchronous QR Code Generation Flow
        User->>+Django: 1. POST /api/qr/generate/ with data
        Django->>+Services: 2. request_qr_generation(data)
        Services->>+PubSub: 3. Publish message to topic
        PubSub-->>-Services: 4. Acknowledge message receipt
        Services-->>-Django: 5. Return success status
        Django-->>-User: 6. HTTP 200 OK (Request received)

        par Asynchronous Background Processing
            PubSub->>+GCF: 7. Trigger function with message
            GCF->>GCF: 8. Generate QR code image
            GCF->>+GCS: 9. Upload QR code image to bucket
            GCS-->>-GCF: 10. Return public URL of the image
            GCF->>+Firestore: 11. Update document with QR code URL
            Firestore-->>-GCF: 12. Acknowledge database update
        end
    end