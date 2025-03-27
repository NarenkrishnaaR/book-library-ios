//
//  ContentView.swift
//  book-library-ios
//
//  Created by Naren on 26/03/25.
//

import SwiftUI
import SwiftData

struct ContentView: View {
  @Environment(\.modelContext) var context
  @Query(sort: \Book.title) var books: [Book]
  
  var body: some View {
    NavigationStack {
      List(books) { book in
        NavigationLink(destination: BookDetailView(book: book)) {
          HStack {
            Text("\(book.title) - \(book.authorName)")
            Spacer()
            if book.isFavourite {
              Image(systemName: "star.fill")
                .foregroundColor(.yellow)
            }
          }
        }
      }
      .navigationTitle("Books")
      .toolbar {
        ToolbarItem(placement: .topBarTrailing) {
          NavigationLink(destination: AddBookView()) {
            Image(systemName: "plus")
          }
        }
      }
    }
    .onAppear {
      migrateData()
    }
  }
  
  private func migrateData() {
    for book in books where book.publishedYear == nil {
      book.publishedYear = "\(book.publicationYear)" // Convert Int32 to String
    }
    try? context.save()
  }
}

#Preview {
  ContentView()
}
