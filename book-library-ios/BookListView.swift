//
//  BookListView.swift
//  book-library-ios
//
//  Created by Naren on 26/03/25.
//

import SwiftUI
import SwiftData

struct BookListView: View {
  @Environment(\.modelContext) var context
  
  @Query(sort: \Book.title) var books: [Book]
  
  @State var searchText = ""
  
  var body: some View {
    NavigationStack {
      List(searchResults) { book in
        NavigationLink(destination: BookDetailView(book: book)) {
          HStack {
            Text("\(book.title!) - \(book.authorName)")
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
    .searchable(text: $searchText)
    .onAppear {
      DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
        m1()
      }
    }
  }
  
  var searchResults: [Book] {
    if searchText.isEmpty {
      return books
    } else {
      return books.filter({$0.title.localizedCaseInsensitiveContains(searchText)})
    }
  }
  
  private func m1() {
    for book in books where book.publishedYear == nil {
      book.publishedYear = "\(book.publicationYear)" // Convert Int32 to String
    }
    try? context.save()
  }
}

#Preview {
  BookListView()
}
