//
//  BookDetailView.swift
//  BookLibrary
//
//  Created by Naren on 27/03/25.
//

import SwiftUI

struct BookDetailView: View {
  let book: Book
  
  var body: some View {
    Form {
      Text("Title - \(book.title)")
      Text("Author Name - \(book.authorName)")
      Text("Publication Year - \(book.publishedYear ?? "")")
      Text("Genre - \(book.genre)")
      Text("Category - \(book.category?.name ?? "")")
    }
  }
}

